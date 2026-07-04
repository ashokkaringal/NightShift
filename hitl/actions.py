"""Manager HITL actions — approve, reject, snooze (Member C)."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from db.engine import SessionLocal
from db.models import DraftRow
from models.core import Draft


def _get_draft(session: Session, draft_id: str) -> DraftRow:
    row = session.get(DraftRow, draft_id)
    if row is None:
        raise ValueError(f"Draft not found: {draft_id}")
    return row


def _to_model(row: DraftRow) -> Draft:
    return Draft(
        id=row.id,
        classified_item_id=row.classified_item_id,
        draft_text=row.draft_text,
        status=row.status,  # type: ignore[arg-type]
        approved_by=row.approved_by,
        approved_at=row.approved_at,
    )


def approve_draft(
    draft_id: str,
    manager: str,
    *,
    session: Session | None = None,
) -> Draft:
    own = session is None
    db = session or SessionLocal()
    try:
        row = _get_draft(db, draft_id)
        row.status = "approved"
        row.approved_by = manager.strip()
        row.approved_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(row)
        return _to_model(row)
    except Exception:
        db.rollback()
        raise
    finally:
        if own:
            db.close()


def edit_and_approve(
    draft_id: str,
    manager: str,
    draft_text: str,
    *,
    session: Session | None = None,
) -> Draft:
    own = session is None
    db = session or SessionLocal()
    try:
        row = _get_draft(db, draft_id)
        row.draft_text = draft_text.strip()
        row.status = "approved"
        row.approved_by = manager.strip()
        row.approved_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(row)
        return _to_model(row)
    except Exception:
        db.rollback()
        raise
    finally:
        if own:
            db.close()


def reject_draft(
    draft_id: str,
    *,
    session: Session | None = None,
) -> Draft:
    own = session is None
    db = session or SessionLocal()
    try:
        row = _get_draft(db, draft_id)
        row.status = "rejected"
        db.commit()
        db.refresh(row)
        return _to_model(row)
    except Exception:
        db.rollback()
        raise
    finally:
        if own:
            db.close()


def save_draft_text(
    draft_id: str,
    draft_text: str,
    *,
    session: Session | None = None,
) -> Draft:
    own = session is None
    db = session or SessionLocal()
    try:
        row = _get_draft(db, draft_id)
        row.draft_text = draft_text.strip()
        db.commit()
        db.refresh(row)
        return _to_model(row)
    except Exception:
        db.rollback()
        raise
    finally:
        if own:
            db.close()


def snooze_draft(
    draft_id: str,
    *,
    session: Session | None = None,
) -> Draft:
    own = session is None
    db = session or SessionLocal()
    try:
        row = _get_draft(db, draft_id)
        row.status = "snoozed"
        db.commit()
        db.refresh(row)
        return _to_model(row)
    except Exception:
        db.rollback()
        raise
    finally:
        if own:
            db.close()
