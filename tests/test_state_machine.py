"""HITL FSM tests — DB CHECK constraint + policy guard."""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from db.engine import SessionLocal
from db.fsm import validate_transition
from db.models import DraftRow
from policy.check_no_send import check_no_send


def test_staged_to_ready_to_send_rejected_by_policy() -> None:
    with pytest.raises(ValueError, match="never auto-sends"):
        check_no_send("staged", "ready_to_send")


def test_staged_to_approved_valid() -> None:
    validate_transition("staged", "approved")


def test_staged_to_sent_rejected() -> None:
    with pytest.raises(ValueError):
        validate_transition("staged", "sent")


def test_db_rejects_invalid_status_on_insert() -> None:
    session = SessionLocal()
    try:
        session.add(
            DraftRow(
                id="draft-invalid",
                classified_item_id="classified-x",
                draft_text="test",
                status="sent",
                approved_by=None,
                approved_at=None,
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
    finally:
        session.rollback()
        session.close()


def test_db_rejects_staged_to_ready_transition() -> None:
    session = SessionLocal()
    try:
        row = DraftRow(
            id="draft-fsm-test",
            classified_item_id="classified-fsm",
            draft_text="hello",
            status="staged",
            approved_by=None,
            approved_at=None,
        )
        session.add(row)
        session.commit()

        row.status = "ready_to_send"
        with pytest.raises(ValueError, match="Invalid transition"):
            session.commit()
    finally:
        session.rollback()
        session.close()
