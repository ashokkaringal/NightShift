"""ResponseAgent — Gemini Pro drafts with rules-template fallback."""

from __future__ import annotations

from sqlalchemy.orm import Session

from agents.response.draft_reply_engine import (
    DraftInput,
    extract_deadline,
    generate_draft_reply_alt,
    infer_source_type,
    show_gas_911_banner,
)
from agents.response.drafter import DraftContext, generate_draft, split_summary
from api.fixture_lookup import enrich_item, resolve_item_property_label
from api.message_format import derive_message_subject
from db.models import DraftRow
from memory.store import get_property_personality
from models.core import ClassifiedItem, Draft

MANAGER_NAME = "Maria Santos"
GREEN_NO_REPLY = "(No tenant reply drafted — GREEN priority per NightShift policy)"
SPAM_NO_REPLY = "(No tenant reply drafted — flagged as SPAM per NightShift policy)"


def build_draft_context(classified: ClassifiedItem) -> tuple[DraftContext, DraftInput]:
    enrich = enrich_item(classified.raw_item_id)
    raw_text = enrich.get("raw_text") or classified.summary
    if not isinstance(raw_text, str):
        raw_text = str(raw_text)
    source = enrich.get("source", "email")
    issue_subject = enrich.get("subject") or derive_message_subject(raw_text, source=source)
    property_name = (
        resolve_item_property_label(
            classified.raw_item_id,
            classified.property_id,
            source,
            raw_text,
        )
        or enrich.get("property_label")
        or "your property"
    )
    summary_line, reasoning = split_summary(classified.summary)
    source_type = infer_source_type(classified.raw_item_id, raw_text, source)

    ctx = DraftContext(
        raw_item_id=classified.raw_item_id,
        urgency=classified.urgency_tier,
        summary=summary_line,
        reasoning=reasoning,
        property_display_name=property_name,
        issue_subject=issue_subject,
        personality_note=get_property_personality(classified.property_id),
        manager_name=MANAGER_NAME,
        source_type=source_type,
        show_911_banner=show_gas_911_banner(raw_text),
        deadline=extract_deadline(raw_text),
    )
    inp = DraftInput(
        urgency=classified.urgency_tier,
        source_type=source_type,
        property_display_name=property_name,
        issue_subject=issue_subject,
        show_911_banner=ctx.show_911_banner,
        manager_name=MANAGER_NAME,
        deadline=ctx.deadline,
    )
    return ctx, inp


def build_draft_text(classified: ClassifiedItem) -> tuple[str, str | None]:
    """Return (draft_text, source_tag) — Gemini model id or rules template_id."""
    if classified.urgency_tier == "SPAM":
        return SPAM_NO_REPLY, None
    if classified.urgency_tier == "GREEN":
        return GREEN_NO_REPLY, None

    ctx, inp = build_draft_context(classified)
    body, source_tag = generate_draft(ctx, inp)
    if not body:
        return GREEN_NO_REPLY, source_tag
    return body, source_tag


def build_draft_variants(classified: ClassifiedItem) -> tuple[str, str | None, str | None]:
    """Return (primary_text, alternate_text, source_tag).

    Primary uses Gemini when available (else rules Option A). The alternate is the
    deterministic rules-based empathetic variant (Option B) so Maria always has a
    second choice; None for GREEN/SPAM which have no tenant reply.
    """
    if classified.urgency_tier in ("SPAM", "GREEN"):
        primary, source_tag = build_draft_text(classified)
        return primary, None, source_tag

    ctx, inp = build_draft_context(classified)
    body, source_tag = generate_draft(ctx, inp)
    if not body:
        return GREEN_NO_REPLY, None, source_tag

    alt_out = generate_draft_reply_alt(inp)
    alternate = alt_out.body if alt_out.status == "DRAFT" and alt_out.body else None
    return body, alternate, source_tag


class ResponseAgent:
    name = "ResponseAgent"

    def run(self, classified: ClassifiedItem, session: Session) -> Draft:
        from observability.tracing import agent_span, set_attributes
        from security.output_validation import assert_draft_output_safe, validate_draft_output

        with agent_span("response", backend=self.backend_name()):
            draft_text, draft_text_alt, _source_tag = build_draft_variants(classified)
            warnings = validate_draft_output(draft_text, classified)
            assert_draft_output_safe(draft_text, classified)
            if draft_text_alt:
                if validate_draft_output(draft_text_alt, classified):
                    # Drop the alternate rather than surface an unsafe/invalid variant.
                    draft_text_alt = None
            if warnings:
                set_attributes(output_validation_warnings=len(warnings))

            draft = Draft(
            id=f"draft-{classified.id}",
            classified_item_id=classified.id,
            draft_text=draft_text,
            draft_text_alt=draft_text_alt,
            status="staged",
            approved_by=None,
            approved_at=None,
        )

        row = DraftRow(
            id=draft.id,
            classified_item_id=draft.classified_item_id,
            raw_item_id=classified.raw_item_id,
            urgency_tier=classified.urgency_tier,
            summary=classified.summary,
            draft_text=draft.draft_text,
            draft_text_alt=draft.draft_text_alt,
            status=draft.status,
            approved_by=draft.approved_by,
            approved_at=draft.approved_at,
        )
        session.add(row)
        session.commit()
        set_attributes(draft_status=draft.status, urgency_tier=classified.urgency_tier)
        return draft

    @staticmethod
    def backend_name() -> str:
        from agents.response.drafter import backend_name as draft_backend

        return draft_backend()
