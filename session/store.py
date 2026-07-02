"""SQLite-backed overnight run state — reconstructable per batch (TDD §2.3, A2b)."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import update
from sqlalchemy.orm import Session

from db.engine import SessionLocal
from db.models import FailedItemRow, OvernightRunRow


class RunStateStore:
    """One ADK/session scope per overnight batch with durable progress."""

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id

    @classmethod
    def start_run(cls, session: Session | None = None) -> RunStateStore:
        own = session is None
        db = session or SessionLocal()
        try:
            run_id = OvernightRunRow.new_id()
            row = OvernightRunRow(
                id=run_id,
                status="running",
                processed=0,
                failed=0,
                started_at=datetime.now(timezone.utc),
            )
            db.add(row)
            db.commit()
            return cls(run_id)
        finally:
            if own:
                db.close()

    @classmethod
    def load(cls, run_id: str) -> RunStateStore | None:
        db = SessionLocal()
        try:
            row = db.get(OvernightRunRow, run_id)
            if row is None:
                return None
            return cls(run_id)
        finally:
            db.close()

    def record_success(self, session: Session | None = None) -> None:
        own = session is None
        db = session or SessionLocal()
        try:
            db.execute(
                update(OvernightRunRow)
                .where(OvernightRunRow.id == self.run_id)
                .values(processed=OvernightRunRow.processed + 1)
            )
            db.commit()
        finally:
            if own:
                db.close()

    def record_failure(
        self,
        raw_item_id: str,
        detail: str,
        session: Session | None = None,
    ) -> None:
        own = session is None
        db = session or SessionLocal()
        try:
            db.execute(
                update(OvernightRunRow)
                .where(OvernightRunRow.id == self.run_id)
                .values(failed=OvernightRunRow.failed + 1)
            )
            db.add(
                FailedItemRow(
                    id=FailedItemRow.new_id(raw_item_id),
                    run_id=self.run_id,
                    raw_item_id=raw_item_id,
                    error_detail=detail[:500],
                    created_at=datetime.now(timezone.utc),
                )
            )
            db.commit()
        finally:
            if own:
                db.close()

    def finish(self, session: Session | None = None) -> OvernightRunRow | None:
        own = session is None
        db = session or SessionLocal()
        try:
            row = db.get(OvernightRunRow, self.run_id)
            if row is None:
                return None
            row.status = "completed"
            row.finished_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(row)
            return row
        finally:
            if own:
                db.close()

    def snapshot(self) -> dict:
        db = SessionLocal()
        try:
            row = db.get(OvernightRunRow, self.run_id)
            if row is None:
                return {"run_id": self.run_id, "status": "missing"}
            failures = (
                db.query(FailedItemRow)
                .filter(FailedItemRow.run_id == self.run_id)
                .all()
            )
            return {
                "run_id": row.id,
                "status": row.status,
                "processed": row.processed,
                "failed": row.failed,
                "started_at": row.started_at.isoformat(),
                "finished_at": row.finished_at.isoformat() if row.finished_at else None,
                "failed_items": [
                    {"raw_item_id": f.raw_item_id, "detail": f.error_detail}
                    for f in failures
                ],
            }
        finally:
            db.close()
