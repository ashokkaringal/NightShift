"""TriageAgent — Day 1 rules stub (LLM on Day 2)."""

from __future__ import annotations

from datetime import datetime, timezone

from memory.store import resolve_property_id
from models.core import ClassifiedItem, RawItem


def _stub_urgency(raw_text: str) -> str:
    text = raw_text.lower()
    if "water stain" in text or "no heat" in text or "code violation" in text:
        return "RED"
    if "invoice" in text or "mismatch" in text or "inspection" in text:
        return "YELLOW"
    return "GREEN"


class TriageAgent:
    name = "TriageAgent"

    def run(self, raw: RawItem) -> ClassifiedItem:
        property_id = resolve_property_id(raw.tenant_id) or "unknown"
        tier = _stub_urgency(raw.raw_text)
        summary = f"{tier} – {raw.raw_text[:120]}..."
        return ClassifiedItem(
            id=f"classified-{raw.id}",
            raw_item_id=raw.id,
            urgency_tier=tier,  # type: ignore[arg-type]
            property_id=property_id,
            summary=summary,
            classified_at=datetime.now(timezone.utc),
        )
