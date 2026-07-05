"""
Rules-first draft-reply engine (NightShift).

Decision tree:
  RED + gas banner     -> red_gas_v1
  RED + source=city    -> red_city_v1
  RED + other          -> red_urgent_v1
  YELLOW               -> yellow_ack_v1
  GREEN / None         -> NO_DRAFT
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

Urgency = Literal["RED", "YELLOW", "GREEN"]
DraftStatus = Literal["DRAFT", "NO_DRAFT"]


@dataclass
class DraftInput:
    urgency: Urgency | None
    source_type: str  # city | tenant | hoa | vendor | inspection | unknown
    property_display_name: str | None = None
    issue_subject: str | None = None  # matches UI subject line / message topic
    show_911_banner: bool = False
    manager_name: str = "Maria Santos"
    deadline: str | None = None


@dataclass
class DraftOutput:
    status: DraftStatus
    template_id: str | None
    body: str | None
    reason: str | None = None


def _greeting(issue_subject: str | None, prop: str) -> str:
    if issue_subject:
        topic = issue_subject[0].lower() + issue_subject[1:] if len(issue_subject) > 1 else issue_subject.lower()
        return f"Hi,\n\nThank you for reaching out about the {topic} at {prop}.\n\n"
    return f"Hi,\n\nThank you for reaching out regarding {prop}.\n\n"


def _deadline_phrase(deadline: str | None) -> str:
    if deadline:
        return f" before {deadline}"
    return " before the stated deadline"


def generate_draft_reply(inp: DraftInput) -> DraftOutput:
    prop = inp.property_display_name or "your property"
    prop_the = inp.property_display_name or "the property"
    issue = inp.issue_subject
    sig = f"— {inp.manager_name}"

    if inp.urgency == "RED":
        if inp.show_911_banner:
            body = (
                _greeting(issue, prop)
                + "We received your report about a possible gas leak. If you have not "
                "already, please leave the unit, do not use electrical switches, and call "
                "911 and the gas utility immediately.\n\n"
                "I am dispatching emergency maintenance now and will follow up shortly.\n\n"
                f"— {inp.manager_name}, Property Management"
            )
            return DraftOutput(status="DRAFT", template_id="red_gas_v1", body=body)

        if inp.source_type == "city":
            topic = issue or "city notice"
            body = (
                _greeting(issue, prop)
                + f"We received the {topic.lower()} for {prop_the}. I am reviewing the stop-work "
                f"order today and will coordinate corrective action{_deadline_phrase(inp.deadline)}.\n\n"
                f"{sig}"
            )
            return DraftOutput(status="DRAFT", template_id="red_city_v1", body=body)

        body = (
            _greeting(issue, prop)
            + "This issue is flagged as urgent. I am scheduling a vendor visit within "
            "24 hours and will confirm the appointment time shortly.\n\n"
            f"{sig}"
        )
        return DraftOutput(status="DRAFT", template_id="red_urgent_v1", body=body)

    if inp.urgency == "YELLOW":
        body = (
            _greeting(issue, prop)
            + "I have logged this for follow-up and will assign the appropriate vendor. "
            "You can expect an update within 1–2 business days.\n\n"
            f"{sig}"
        )
        return DraftOutput(status="DRAFT", template_id="yellow_ack_v1", body=body)

    return DraftOutput(
        status="NO_DRAFT",
        template_id=None,
        body=None,
        reason="GREEN or unrated — no reply needed",
    )


def generate_draft_reply_alt(inp: DraftInput) -> DraftOutput:
    """Empathetic alternate variant (Option B) — warmer tone, interim help.

    Mirrors the primary decision tree; only wording differs so Maria can pick.
    """
    prop = inp.property_display_name or "your property"
    prop_the = inp.property_display_name or "the property"
    issue = inp.issue_subject
    sig = f"— {inp.manager_name}"

    if inp.urgency == "RED":
        if inp.show_911_banner:
            body = (
                _greeting(issue, prop)
                + "I'm so sorry — a possible gas leak is frightening. Your safety comes "
                "first: if you haven't already, please leave the unit now, avoid using any "
                "electrical switches, and call 911 and the gas utility right away.\n\n"
                "I have emergency maintenance on the way and will stay reachable until you're "
                "safe and the issue is resolved.\n\n"
                f"— {inp.manager_name}, Property Management"
            )
            return DraftOutput(status="DRAFT", template_id="red_gas_v2_empathetic", body=body)

        if inp.source_type == "city":
            topic = issue or "city notice"
            body = (
                _greeting(issue, prop)
                + f"Thank you for flagging the {topic.lower()} for {prop_the} — I understand "
                "how stressful an official notice can feel. I'm personally reviewing the "
                f"stop-work order today and will coordinate every corrective step needed"
                f"{_deadline_phrase(inp.deadline)}. I'll keep you updated so nothing catches "
                "you by surprise.\n\n"
                f"{sig}"
            )
            return DraftOutput(status="DRAFT", template_id="red_city_v2_empathetic", body=body)

        body = (
            _greeting(issue, prop)
            + "I'm sorry you're dealing with this — I know it's urgent and I've made it a "
            "priority. I'm contacting our vendor now and will confirm a visit window within "
            "the next few hours. If things get worse in the meantime, please reach out and "
            "we'll arrange interim help.\n\n"
            f"{sig}"
        )
        return DraftOutput(status="DRAFT", template_id="red_urgent_v2_empathetic", body=body)

    if inp.urgency == "YELLOW":
        body = (
            _greeting(issue, prop)
            + "Thank you for letting me know — I appreciate your patience. I've logged this "
            "and will assign the right vendor to take care of it. You can expect a personal "
            "update from me within 1–2 business days, and I'm happy to answer any questions "
            "in the meantime.\n\n"
            f"{sig}"
        )
        return DraftOutput(status="DRAFT", template_id="yellow_ack_v2_empathetic", body=body)

    return DraftOutput(
        status="NO_DRAFT",
        template_id=None,
        body=None,
        reason="GREEN or unrated — no reply needed",
    )


_MONTH = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"
_WEEKDAY = r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)"
_YEAR = r"\d{4}"


def extract_deadline(raw_text: str) -> str | None:
    """Best-effort deadline phrase — prefers full dates from PDFs over weekday-only hints."""
    candidates: list[tuple[int, str]] = []

    for match in re.finditer(r"compliance\s+deadline:\s*([^\n]+)", raw_text, re.IGNORECASE):
        candidates.append((100, match.group(1).strip()))

    for match in re.finditer(r"(?<![a-z])deadline:\s*([^\n]+)", raw_text, re.IGNORECASE):
        phrase = match.group(1).strip()
        if phrase and not phrase.lower().startswith("compliance"):
            candidates.append((92, phrase))

    for match in re.finditer(
        rf"\bby\s+({_WEEKDAY}\s+{_MONTH}\s+\d{{1,2}}\s+{_YEAR})",
        raw_text,
        re.IGNORECASE,
    ):
        candidates.append((94, match.group(1).strip()))

    for match in re.finditer(
        rf"\bby\s+({_MONTH}\s+\d{{1,2}}(?:,?\s+{_YEAR})?)",
        raw_text,
        re.IGNORECASE,
    ):
        candidates.append((90, match.group(1).strip()))

    for match in re.finditer(r"\bby\s+(\d{4}-\d{2}-\d{2})", raw_text, re.IGNORECASE):
        candidates.append((88, match.group(1).strip()))

    for match in re.finditer(
        r"\b(resolve|complete|repair)\s+by\s+([^.\n]+)",
        raw_text,
        re.IGNORECASE,
    ):
        candidates.append((80, match.group(2).strip()))

    for match in re.finditer(rf"\bby\s+({_WEEKDAY})\b", raw_text, re.IGNORECASE):
        candidates.append((35, match.group(1).strip()))

    if not candidates:
        return None

    candidates.sort(key=lambda item: (-item[0], -len(item[1])))
    top_score = candidates[0][0]
    top = [phrase for score, phrase in candidates if score == top_score]
    with_year = [phrase for phrase in top if re.search(_YEAR, phrase)]
    return with_year[0] if with_year else top[0]


def infer_source_type(raw_item_id: str, raw_text: str, fixture_source: str | None) -> str:
    text = raw_text.lower()
    if any(k in text for k in ("code violation", "city notice", "stop-work", "stop work")):
        return "city"
    if fixture_source == "hoa_portal" or raw_item_id.startswith("hoa"):
        return "hoa"
    if fixture_source == "invoice" or raw_item_id.startswith("invoice"):
        return "vendor"
    if "inspection" in text or "fire alarm" in text:
        return "inspection"
    if fixture_source == "email" or raw_item_id.startswith("email"):
        return "tenant"
    return "unknown"


def show_gas_911_banner(raw_text: str) -> bool:
    text = raw_text.lower()
    return "gas" in text and any(k in text for k in ("smell", "odor", "leak", "stove"))
