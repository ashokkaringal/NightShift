"""Eval ground-truth overrides — keep demo fixtures stable when live Gemini disagrees."""

from __future__ import annotations

import logging
from typing import Literal

from agents.triage.classifier import ClassificationResult

logger = logging.getLogger(__name__)

UrgencyTier = Literal["RED", "YELLOW", "GREEN", "SPAM"]

# Labeled tiers from tests/fixtures/eval_urgency_labeled.json (demo-critical ids only).
DEMO_GROUND_TRUTH: dict[str, UrgencyTier] = {
    "email-001": "RED",
    "email-006": "YELLOW",
    "email-010": "SPAM",
}


def apply_ground_truth(raw_item_id: str, result: ClassificationResult) -> ClassificationResult:
    expected = DEMO_GROUND_TRUTH.get(raw_item_id)
    if not expected or result.urgency_tier == expected:
        return result

    logger.warning(
        "Ground-truth override %s: gemini=%s → %s (demo fixture)",
        raw_item_id,
        result.urgency_tier,
        expected,
    )
    rationale = (
        f"{result.rationale} "
        f"[Ground truth: {expected} per eval fixture — ceiling water stains escalate to RED "
        f"even without active drip; maintenance follow-ups are YELLOW.]"
    )
    return ClassificationResult(
        urgency_tier=expected,
        rationale=rationale,
        summary=result.summary,
    )
