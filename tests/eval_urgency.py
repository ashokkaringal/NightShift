"""Urgency eval — hard case email-001 must be RED."""

from __future__ import annotations

import json
from pathlib import Path

from agents.triage.agent import TriageAgent
from models.core import RawItem

FIXTURES = Path(__file__).parent / "fixtures" / "inbox_test.json"


def _load_items() -> list[RawItem]:
    data = json.loads(FIXTURES.read_text())
    return [RawItem.model_validate(item) for item in data]


def test_water_stain_hard_case_is_red() -> None:
    items = _load_items()
    hard = next(i for i in items if i.id == "email-001")
    classified = TriageAgent().run(hard)
    assert classified.urgency_tier == "RED", classified.summary


def test_lightbulb_is_green() -> None:
    items = _load_items()
    item = next(i for i in items if i.id == "email-002")
    classified = TriageAgent().run(item)
    assert classified.urgency_tier == "GREEN"
