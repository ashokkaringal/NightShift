"""Member A platform tests — ingestion, run state, failure isolation."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from agents.ingestion.agent import IngestionAgent
from agents.supervisor import SupervisorNode
from db.engine import SessionLocal
from db.models import FailedItemRow
from mcp.loaders import ingest_all_sources
from models.core import RawItem
from session.store import RunStateStore


def test_mcp_ingest_at_least_ten_items() -> None:
    items = ingest_all_sources()
    sources = {i.source for i in items}
    assert len(items) >= 10
    assert sources == {"email", "hoa_portal", "invoice"}
    assert any(i.id == "email-001" for i in items)


def test_overnight_run_persisted_to_sqlite() -> None:
    run = RunStateStore.start_run()
    run.record_success()
    run.record_success()
    finished = run.finish()
    assert finished is not None
    assert finished.status == "completed"
    assert finished.processed == 2

    loaded = RunStateStore.load(run.run_id)
    assert loaded is not None
    snap = loaded.snapshot()
    assert snap["processed"] == 2
    assert snap["status"] == "completed"


def test_failure_isolation_does_not_halt_batch() -> None:
    from datetime import datetime, timezone

    from agents.triage.agent import TriageAgent as RealTriage

    good = RawItem(
        id="email-002",
        source="email",
        tenant_id="tenant-456",
        raw_text="Lightbulb in hallway is out, no rush.",
        received_at=datetime(2026, 6, 29, 22, 40, tzinfo=timezone.utc),
    )
    bad = RawItem(
        id="email-broken",
        source="email",
        tenant_id="tenant-123",
        raw_text="This item will fail triage in tests.",
        received_at=datetime(2026, 6, 29, 22, 0, tzinfo=timezone.utc),
    )

    _orig_run = RealTriage.run

    def _side(raw: RawItem):
        if raw.id == "email-broken":
            raise RuntimeError("simulated MCP/triage failure")
        return _orig_run(RealTriage(), raw)

    with patch.object(RealTriage, "run", side_effect=_side):
        supervisor = SupervisorNode()
        results = supervisor.run_batch([bad, good])

    assert len(results) == 2
    assert any(r["raw_item_id"] == "email-broken" and r["error"] == "triage_failed" for r in results)
    assert any(r["raw_item_id"] == "email-002" and r["classified"] is not None for r in results)

    snap = supervisor.run_state.snapshot()
    assert snap["failed"] >= 1
    assert snap["processed"] >= 1

    session = SessionLocal()
    try:
        rows = session.query(FailedItemRow).filter(FailedItemRow.run_id == snap["run_id"]).all()
        assert any(r.raw_item_id == "email-broken" for r in rows)
    finally:
        session.close()


def test_adk_graph_has_three_named_sub_agents() -> None:
    from agents.adk.graph import root_agent

    names = [a.name for a in root_agent.sub_agents]
    assert names == ["IngestionAgent", "TriageAgent", "ResponseAgent"]


def test_ingestion_agent_dedupes_via_loaders() -> None:
    items = IngestionAgent().run()
    ids = [i.id for i in items]
    assert len(ids) == len(set(ids))
