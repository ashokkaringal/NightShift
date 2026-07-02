"""SQLAlchemy models with HITL CHECK constraint (TDD §2.5)."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, event, inspect
from sqlalchemy.orm import Mapped, mapped_column

from db.engine import Base
from db.fsm import validate_transition

VALID_STATUSES = (
    "staged",
    "approved",
    "rejected",
    "snoozed",
    "ready_to_send",
)


class OvernightRunRow(Base):
    """One row per overnight batch — shared run context (A2b)."""

    __tablename__ = "overnight_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="running")
    processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('running', 'completed', 'failed')",
            name="overnight_run_status_valid",
        ),
    )

    @staticmethod
    def new_id() -> str:
        return uuid4().hex[:12]


class FailedItemRow(Base):
    """Items that could not be classified/drafted — visible in Morning Brief (A6)."""

    __tablename__ = "failed_items"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(String, ForeignKey("overnight_runs.id"), nullable=False)
    raw_item_id: Mapped[str] = mapped_column(String, nullable=False)
    error_detail: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    @staticmethod
    def new_id(raw_item_id: str) -> str:
        return f"fail-{raw_item_id}-{uuid4().hex[:8]}"


class DraftRow(Base):
    __tablename__ = "drafts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    classified_item_id: Mapped[str] = mapped_column(String, nullable=False)
    draft_text: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    approved_by: Mapped[str | None] = mapped_column(String, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('staged', 'approved', 'rejected', 'snoozed', 'ready_to_send')",
            name="draft_status_valid",
        ),
    )


@event.listens_for(DraftRow, "before_update")
def _enforce_fsm(_mapper: object, _connection: object, target: DraftRow) -> None:
    state = inspect(target)
    history = state.attrs.status.history
    if not history.has_changes():
        return
    old_status = history.deleted[0] if history.deleted else target.status
    new_status = history.added[0] if history.added else target.status
    validate_transition(old_status, new_status)
