"""Member C tests — HITL actions, morning brief, failed items."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from brief.assembler import assemble_brief, format_brief_text
from db.engine import SessionLocal
from db.models import DraftRow, FailedItemRow, OvernightRunRow


def _clear_brief_tables(session) -> None:
    session.query(FailedItemRow).delete()
    session.query(DraftRow).delete()
    session.query(OvernightRunRow).delete()
    session.commit()
from hitl.actions import approve_draft, reject_draft, snooze_draft


def _seed_run(session, run_id: str = "run-test-001") -> OvernightRunRow:
    row = OvernightRunRow(
        id=run_id,
        status="completed",
        processed=2,
        failed=1,
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
    )
    session.add(row)
    session.commit()
    return row


def _seed_draft(
    session,
    *,
    draft_id: str,
    raw_item_id: str,
    tier: str,
    summary: str,
    text: str,
    status: str = "staged",
) -> DraftRow:
    row = DraftRow(
        id=draft_id,
        classified_item_id=f"classified-{raw_item_id}",
        raw_item_id=raw_item_id,
        urgency_tier=tier,
        summary=summary,
        draft_text=text,
        status=status,
        approved_by=None,
        approved_at=None,
    )
    session.add(row)
    session.commit()
    return row


def test_approve_requires_manager_identity() -> None:
    session = SessionLocal()
    try:
        _seed_draft(
            session,
            draft_id="draft-approve-test",
            raw_item_id="email-001",
            tier="RED",
            summary="Water stain | Reasoning: structural risk",
            text="We will schedule an inspection.",
        )
        draft = approve_draft("draft-approve-test", "Jane Doe", session=session)
        assert draft.status == "approved"
        assert draft.approved_by == "Jane Doe"
        assert draft.approved_at is not None
    finally:
        session.close()


def test_approve_without_manager_metadata_rejected() -> None:
    session = SessionLocal()
    try:
        _clear_brief_tables(session)
        row = _seed_draft(
            session,
            draft_id="draft-bad-approve",
            raw_item_id="email-002",
            tier="GREEN",
            summary="Lightbulb",
            text="Thanks for reporting.",
        )
        row.status = "approved"
        with pytest.raises(ValueError, match="approved_by"):
            session.commit()
        session.rollback()
    finally:
        session.close()


def test_morning_brief_orders_red_first() -> None:
    session = SessionLocal()
    try:
        _clear_brief_tables(session)
        _seed_run(session)
        _seed_draft(
            session,
            draft_id="draft-green",
            raw_item_id="email-008",
            tier="GREEN",
            summary="Package room",
            text="Low priority ack",
        )
        _seed_draft(
            session,
            draft_id="draft-red",
            raw_item_id="email-001",
            tier="RED",
            summary="Water stain | Reasoning: early damage",
            text="Urgent inspection scheduled",
        )
        _seed_draft(
            session,
            draft_id="draft-yellow",
            raw_item_id="email-006",
            tier="YELLOW",
            summary="Faucet follow-up",
            text="Following up on maintenance",
        )

        brief = assemble_brief(session=session)
        tiers = [d.urgency_tier for d in brief.drafts]
        assert tiers == ["RED", "YELLOW", "GREEN"]
        text = format_brief_text(brief)
        assert "email-001" in text
        assert "Reasoning:" in text
    finally:
        session.close()


def test_morning_brief_shows_triage_failed_items() -> None:
    session = SessionLocal()
    try:
        _clear_brief_tables(session)
        run = _seed_run(session, run_id="run-fail-001")
        session.add(
            FailedItemRow(
                id="fail-email-broken",
                run_id=run.id,
                raw_item_id="email-broken",
                error_detail="simulated triage failure",
                created_at=datetime.now(timezone.utc),
            )
        )
        session.commit()

        brief = assemble_brief(session=session)
        assert len(brief.failed) == 1
        assert brief.failed[0].raw_item_id == "email-broken"
        text = format_brief_text(brief)
        assert "COULD NOT CLASSIFY" in text
        assert "email-broken" in text
    finally:
        session.close()


def test_reject_and_snooze_transitions() -> None:
    session = SessionLocal()
    try:
        _seed_draft(
            session,
            draft_id="draft-reject",
            raw_item_id="email-004",
            tier="GREEN",
            summary="Newsletter",
            text="No reply needed",
        )
        rejected = reject_draft("draft-reject", session=session)
        assert rejected.status == "rejected"

        _seed_draft(
            session,
            draft_id="draft-snooze",
            raw_item_id="email-006",
            tier="YELLOW",
            summary="Faucet",
            text="Will check tomorrow",
        )
        snoozed = snooze_draft("draft-snooze", session=session)
        assert snoozed.status == "snoozed"
    finally:
        session.close()
