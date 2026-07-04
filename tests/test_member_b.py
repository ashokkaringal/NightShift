"""Member B tests — memory, classification contracts, eval harness."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.response.agent import build_draft_context
from agents.triage.agent import TriageAgent
from memory.consolidate import consolidate
from memory.store import get_property_personality, resolve_property_id
from models.core import ClassifiedItem, Draft
from tests.eval_urgency import load_labeled_cases

FIXTURES = Path(__file__).parent / "fixtures" / "eval_urgency_labeled.json"


def test_memory_lookup_returns_property_id() -> None:
    assert resolve_property_id("tenant-123") == "property-A"
    assert resolve_property_id("tenant456@example.com") == "property-B"


def test_memory_lookup_miss_is_explicit_none() -> None:
    assert resolve_property_id("tenant-unknown") is None
    assert resolve_property_id(None) is None


def test_classified_item_has_no_raw_text_field() -> None:
    cases = load_labeled_cases()
    classified = TriageAgent().run(cases[0].item)
    assert isinstance(classified, ClassifiedItem)
    assert not hasattr(classified, "raw_text")
    assert "raw_text" not in classified.model_dump()


def test_draft_model_has_no_raw_text_field() -> None:
    draft = Draft(id="draft-1", classified_item_id="classified-1", draft_text="Hello")
    assert not hasattr(draft, "raw_text")
    assert "raw_text" not in draft.model_dump()


def test_hard_case_includes_reasoning_trace() -> None:
    cases = load_labeled_cases()
    hard = next(c for c in cases if c.id == "email-001")
    classified = TriageAgent().run(hard.item)
    assert classified.urgency_tier == "RED"
    assert "Reasoning:" in classified.summary
    assert "water stain" in hard.item.raw_text.lower()


def test_eval_fixture_file_has_twenty_plus_rows() -> None:
    data = json.loads(FIXTURES.read_text(encoding="utf-8"))
    assert len(data) >= 20
    tiers = {row["expected_urgency_tier"] for row in data}
    assert tiers == {"RED", "YELLOW", "GREEN"}


def test_memory_consolidation_merges_incoming(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "tenant_property_map.json").write_text("[]", encoding="utf-8")

    incoming = tmp_path / "incoming"
    incoming.mkdir()
    (incoming / "tenant_property_map.json").write_text(
        json.dumps(
            [
                {
                    "tenant_id": "tenant-999",
                    "tenant_email": "new@example.com",
                    "property_id": "property-Z",
                }
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr("memory.store.DATA_DIR", data_dir)
    stats = consolidate(incoming, data_dir=data_dir)
    assert stats["merged"] == 1

    from memory.store import resolve_property_id

    assert resolve_property_id("tenant-999") == "property-Z"


def test_memory_lookup_success_rate_on_tenant_fixtures() -> None:
    """PRD §1.3 — ≥98% tenant-tied fixtures resolve to a property_id."""
    cases = load_labeled_cases()
    tenant_cases = [c for c in cases if c.item.tenant_id]
    assert tenant_cases, "expected tenant-tied eval fixtures"

    resolved = sum(1 for c in tenant_cases if resolve_property_id(c.item.tenant_id))
    rate = resolved / len(tenant_cases)
    assert rate >= 0.98, f"memory lookup {rate:.1%} below 98% target"


def test_response_agent_uses_property_personality_note() -> None:
    cases = load_labeled_cases()
    hard = next(c for c in cases if c.id == "email-001")
    classified = TriageAgent().run(hard.item)
    ctx, _ = build_draft_context(classified)

    expected = get_property_personality("property-A")
    assert expected is not None
    assert ctx.personality_note == expected
