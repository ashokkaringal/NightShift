"""Gemini Pro drafting with rules-template fallback (Member C)."""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass

from agents.gemini_client import generate_content, model_candidates
from agents.gemini_config import has_api_key, in_live_subset
from agents.response.draft_reply_engine import DraftInput, DraftOutput, generate_draft_reply
from agents.response.prompts import DRAFTING_SYSTEM

logger = logging.getLogger(__name__)

# Pro first for submission narrative; Flash fallback on free tier (Pro often has 0 quota).
DEFAULT_DRAFT_MODEL = os.getenv("GEMINI_DRAFT_MODEL", "gemini-2.5-flash").split(",")[0].strip()
DRAFT_MODEL_CANDIDATES = model_candidates(
    "GEMINI_DRAFT_MODEL",
    "gemini-2.5-flash,gemini-3.5-flash",
)
# Omit max_output_tokens by default — low caps truncate gemini-2.5-* replies (MAX_TOKENS).
_raw_max = os.getenv("GEMINI_DRAFT_MAX_TOKENS", "").strip()
DEFAULT_MAX_OUTPUT_TOKENS: int | None = int(_raw_max) if _raw_max else None


@dataclass
class DraftContext:
    raw_item_id: str
    urgency: str
    summary: str
    reasoning: str | None
    property_display_name: str
    issue_subject: str | None
    personality_note: str | None
    manager_name: str
    source_type: str
    show_911_banner: bool
    deadline: str | None


def use_gemini_drafter(raw_item_id: str | None = None) -> bool:
    if os.getenv("DRAFT_USE_STUB", "").lower() in {"1", "true", "yes"}:
        return False
    if not has_api_key():
        return False
    return in_live_subset(raw_item_id)


def backend_name() -> str:
    if os.getenv("DRAFT_USE_STUB", "").lower() in {"1", "true", "yes"}:
        return "rules-template"
    if has_api_key():
        return " → ".join(DRAFT_MODEL_CANDIDATES)
    return "rules-template"


def split_summary(summary: str) -> tuple[str, str | None]:
    if "| Reasoning:" in summary:
        left, _, right = summary.partition("| Reasoning:")
        return left.strip(), right.strip()
    return summary.strip(), None


def draft_with_rules(inp: DraftInput) -> DraftOutput:
    return generate_draft_reply(inp)


def _build_user_prompt(ctx: DraftContext) -> str:
    lines = [
        f"Urgency: {ctx.urgency}",
        f"Property: {ctx.property_display_name}",
    ]
    if ctx.issue_subject:
        lines.append(f"Issue topic: {ctx.issue_subject}")
    lines.append(f"Summary: {ctx.summary}")
    if ctx.reasoning:
        lines.append(f"Triage reasoning: {ctx.reasoning}")
    if ctx.personality_note:
        lines.append(f"Property context: {ctx.personality_note}")
    lines.append(f"Source: {ctx.source_type}")
    if ctx.deadline:
        lines.append(f"Deadline mentioned: {ctx.deadline}")
    if ctx.show_911_banner:
        lines.append("Gas emergency: yes — include 911 and gas utility safety steps.")
    lines.append(f"Sign as: {ctx.manager_name}")
    return "\n".join(lines)


def _clean_body(text: str, manager_name: str) -> str:
    body = text.strip()
    if body.startswith("```"):
        body = re.sub(r"^```(?:\w+)?\s*", "", body)
        body = re.sub(r"\s*```$", "", body).strip()
    if manager_name and manager_name not in body:
        body = f"{body}\n\n— {manager_name}"
    return body


def draft_with_gemini(ctx: DraftContext) -> tuple[str, str]:
    system = DRAFTING_SYSTEM.replace("{manager_name}", ctx.manager_name)
    body, model_used = generate_content(
        models=DRAFT_MODEL_CANDIDATES,
        contents=_build_user_prompt(ctx),
        system_instruction=system,
        max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS,
    )
    return _clean_body(body, ctx.manager_name), model_used


def generate_draft(ctx: DraftContext, inp: DraftInput) -> tuple[str, str | None]:
    """Return (draft_text, source_tag) where source_tag is model id or template_id."""
    rules_out = draft_with_rules(inp)
    if rules_out.status == "NO_DRAFT" or not rules_out.body:
        return "", rules_out.template_id

    if use_gemini_drafter(ctx.raw_item_id):
        try:
            body, model_used = draft_with_gemini(ctx)
            logger.info(
                "Draft %s via %s (%d chars)",
                ctx.raw_item_id,
                model_used,
                len(body),
            )
            return body, model_used
        except Exception as exc:  # noqa: BLE001 — bounded fallback
            logger.warning(
                "Gemini draft failed for %s (%s), using rules template",
                ctx.raw_item_id,
                exc,
            )

    return rules_out.body, rules_out.template_id
