"""TriageAgent — Gemini Flash classification with rules fallback (Member B)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from agents.triage.classifier import classify_urgency, use_gemini_classifier
from memory.store import resolve_property_id
from models.core import ClassifiedItem, RawItem

logger = logging.getLogger(__name__)


class TriageAgent:
    name = "TriageAgent"

    def run(self, raw: RawItem) -> ClassifiedItem:
        property_id = resolve_property_id(raw.tenant_id) or "unknown"
        result = classify_urgency(raw.raw_text, property_id)

        summary = f"{result.summary} | Reasoning: {result.rationale}"
        if raw.id == "email-001":
            logger.info(
                "Hard case email-001 classified %s — %s",
                result.urgency_tier,
                result.rationale,
            )

        return ClassifiedItem(
            id=f"classified-{raw.id}",
            raw_item_id=raw.id,
            urgency_tier=result.urgency_tier,
            property_id=property_id,
            summary=summary,
            classified_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def backend_name() -> str:
        return "gemini-flash" if use_gemini_classifier() else "rules-stub"
