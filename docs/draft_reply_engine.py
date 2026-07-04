"""
Portable draft-reply engine (from NightShift).
Copy this single file into any project — no other NightShift imports required.

Usage:
    from draft_reply_engine import generate_draft_reply, DraftInput

    draft = generate_draft_reply(DraftInput(
        urgency="RED",
        source_type="city",
        property_display_name="Oak Street Duplex",
        show_911_banner=False,
        manager_name="Maria Santos",
    ))
    print(draft.body)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Urgency = Literal["RED", "YELLOW", "GREEN"]
DraftStatus = Literal["DRAFT", "NO_DRAFT"]


@dataclass
class DraftInput:
    """Minimum fields needed to pick a template and fill placeholders."""

    urgency: Urgency | None
    source_type: str  # city | tenant | hoa | vendor | inspection | unknown
    property_display_name: str | None = None
    show_911_banner: bool = False
    manager_name: str = "Maria Santos"
    deadline: str | None = None  # optional: from extraction, e.g. "June 27, 2026"


@dataclass
class DraftOutput:
    status: DraftStatus
    template_id: str | None
    body: str | None
    reason: str | None = None


def _greeting(prop: str) -> str:
    return f"Hi,\n\nThank you for reaching out regarding {prop}.\n\n"


def _deadline_phrase(deadline: str | None) -> str:
    if deadline:
        return f" before {deadline}"
    return " before the stated deadline"


def generate_draft_reply(inp: DraftInput) -> DraftOutput:
    """
    Rules-first draft selection (no LLM).

    Decision tree:
      RED + gas banner     -> red_gas_v1
      RED + source=city    -> red_city_v1
      RED + other          -> red_urgent_v1
      YELLOW               -> yellow_ack_v1
      GREEN / None         -> NO_DRAFT
    """
    prop = inp.property_display_name or "your property"
    prop_the = inp.property_display_name or "the property"
    sig = f"— {inp.manager_name}"

    if inp.urgency == "RED":
        if inp.show_911_banner:
            body = (
                _greeting(prop)
                + "We received your report about a possible gas leak. If you have not "
                "already, please leave the unit, do not use electrical switches, and call "
                "911 and the gas utility immediately.\n\n"
                "I am dispatching emergency maintenance now and will follow up shortly.\n\n"
                f"— {inp.manager_name}, Property Management"
            )
            return DraftOutput(status="DRAFT", template_id="red_gas_v1", body=body)

        if inp.source_type == "city":
            body = (
                _greeting(prop)
                + f"We received the city notice for {prop_the}. I am reviewing the stop-work "
                f"order today and will coordinate corrective action{_deadline_phrase(inp.deadline)}.\n\n"
                f"{sig}"
            )
            return DraftOutput(status="DRAFT", template_id="red_city_v1", body=body)

        body = (
            _greeting(prop)
            + "This issue is flagged as urgent. I am scheduling a vendor visit within "
            "24 hours and will confirm the appointment time shortly.\n\n"
            f"{sig}"
        )
        return DraftOutput(status="DRAFT", template_id="red_urgent_v1", body=body)

    if inp.urgency == "YELLOW":
        body = (
            _greeting(prop)
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


# --- Example / self-test ---
if __name__ == "__main__":
    examples = [
        DraftInput(
            urgency="RED",
            source_type="city",
            property_display_name="Oak Street Duplex",
        ),
        DraftInput(
            urgency="RED",
            source_type="tenant",
            property_display_name="Valencia Condo",
            show_911_banner=True,
        ),
        DraftInput(urgency="YELLOW", source_type="tenant", property_display_name="Haight Cottage"),
        DraftInput(urgency="GREEN", source_type="vendor", property_display_name="16th Street Fourplex"),
    ]
    for ex in examples:
        out = generate_draft_reply(ex)
        print("=" * 60)
        print(f"urgency={ex.urgency} source={ex.source_type} -> {out.template_id}")
        print(out.body or out.reason)
        print()
