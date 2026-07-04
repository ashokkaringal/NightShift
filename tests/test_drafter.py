"""Tests for Gemini Pro drafter + token-saving live subset."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from agents.gemini_config import in_live_subset, live_only_ids
from agents.response.drafter import (
    DEFAULT_DRAFT_MODEL,
    DraftContext,
    draft_with_rules,
    generate_draft,
    use_gemini_drafter,
)
from agents.response.draft_reply_engine import DraftInput


def _sample_context(**overrides: object) -> DraftContext:
    base = {
        "raw_item_id": "email-001",
        "urgency": "RED",
        "summary": "RED – water stain",
        "reasoning": "Early structural water-damage pattern.",
        "property_display_name": "Oak Street Duplex",
        "issue_subject": "Bathroom ceiling water stain",
        "personality_note": "Older building, high-maintenance HVAC.",
        "manager_name": "Maria Santos",
        "source_type": "tenant",
        "show_911_banner": False,
        "deadline": None,
    }
    base.update(overrides)
    return DraftContext(**base)  # type: ignore[arg-type]


def _sample_input() -> DraftInput:
    return DraftInput(
        urgency="RED",
        source_type="tenant",
        property_display_name="Oak Street Duplex",
        issue_subject="Bathroom ceiling water stain",
    )


def test_live_only_ids_filters_subset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_LIVE_ONLY_IDS", "email-001,email-006")
    assert live_only_ids() == frozenset({"email-001", "email-006"})
    assert in_live_subset("email-001") is True
    assert in_live_subset("email-002") is False


def test_use_gemini_drafter_respects_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("DRAFT_USE_STUB", "1")
    assert use_gemini_drafter("email-001") is False


def test_use_gemini_drafter_respects_live_subset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.delenv("DRAFT_USE_STUB", raising=False)
    monkeypatch.setenv("GEMINI_LIVE_ONLY_IDS", "email-001")
    assert use_gemini_drafter("email-001") is True
    assert use_gemini_drafter("email-002") is False


@patch("agents.response.drafter.draft_with_gemini")
def test_generate_draft_prefers_gemini(mock_gemini: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    mock_gemini.return_value = ("Hi,\n\nPro draft body.\n\n— Maria Santos", "gemini-test")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.delenv("DRAFT_USE_STUB", raising=False)

    body, tag = generate_draft(_sample_context(), _sample_input())
    assert "Pro draft body" in body
    assert tag  # model id returned by mock
    mock_gemini.assert_called_once()


@patch("agents.response.drafter.draft_with_gemini", side_effect=RuntimeError("api down"))
def test_generate_draft_falls_back_to_rules(mock_gemini: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.delenv("DRAFT_USE_STUB", raising=False)

    body, tag = generate_draft(_sample_context(), _sample_input())
    assert "bathroom ceiling water stain" in body.lower()
    assert tag == "red_urgent_v1"
    mock_gemini.assert_called_once()


def test_draft_with_rules_unchanged_for_green() -> None:
    out = draft_with_rules(
        DraftInput(urgency="GREEN", source_type="tenant", property_display_name="Oak Street Duplex")
    )
    assert out.status == "NO_DRAFT"


@pytest.mark.skipif(
    not __import__("os").getenv("GEMINI_API_KEY")
    or __import__("os").getenv("DRAFT_USE_STUB", "").lower() in {"1", "true"},
    reason="Set GEMINI_API_KEY and unset DRAFT_USE_STUB for live Pro draft test",
)
def test_gemini_live_draft_hard_case(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_LIVE_ONLY_IDS", "email-001")
    from agents.response.agent import build_draft_text
    from models.core import ClassifiedItem
    from datetime import datetime, timezone

    classified = ClassifiedItem(
        id="classified-email-001",
        raw_item_id="email-001",
        urgency_tier="RED",
        property_id="property-A",
        summary="RED – water stain | Reasoning: structural risk",
        classified_at=datetime.now(timezone.utc),
    )
    text, tag = build_draft_text(classified)
    assert tag and tag.startswith("gemini")
    assert "Maria Santos" in text
    assert "oak street" in text.lower() or "water stain" in text.lower()
