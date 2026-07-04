"""Tests for demo ground-truth tier overrides."""

from __future__ import annotations

from agents.triage.classifier import ClassificationResult
from agents.triage.ground_truth import apply_ground_truth


def test_email_001_override_yellow_to_red() -> None:
    result = ClassificationResult(
        urgency_tier="YELLOW",
        rationale="No active drip.",
        summary="Water stain",
    )
    out = apply_ground_truth("email-001", result)
    assert out.urgency_tier == "RED"
    assert "Ground truth" in out.rationale


def test_email_006_override_green_to_yellow() -> None:
    result = ClassificationResult(
        urgency_tier="GREEN",
        rationale="Not urgent.",
        summary="Faucet follow-up",
    )
    out = apply_ground_truth("email-006", result)
    assert out.urgency_tier == "YELLOW"


def test_non_demo_id_unchanged() -> None:
    result = ClassificationResult(
        urgency_tier="GREEN",
        rationale="Newsletter.",
        summary="HOA pool",
    )
    out = apply_ground_truth("email-004", result)
    assert out.urgency_tier == "GREEN"
