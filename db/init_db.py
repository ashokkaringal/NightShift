"""Initialize database tables."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import inspect, text

from db.engine import Base, engine
from db.models import DraftRow, FailedItemRow, OvernightRunRow  # noqa: F401

_DRAFT_OPTIONAL_COLUMNS = (
    ("raw_item_id", "TEXT"),
    ("urgency_tier", "TEXT"),
    ("summary", "TEXT"),
)


def _migrate_draft_columns() -> None:
    """Add brief columns to existing SQLite DBs (create_all does not alter tables)."""
    inspector = inspect(engine)
    if "drafts" not in inspector.get_table_names():
        return
    existing = {col["name"] for col in inspector.get_columns("drafts")}
    with engine.begin() as conn:
        for name, col_type in _DRAFT_OPTIONAL_COLUMNS:
            if name not in existing:
                conn.execute(text(f"ALTER TABLE drafts ADD COLUMN {name} {col_type}"))


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _migrate_draft_columns()


if __name__ == "__main__":
    init_db()
    print("Database tables created.")
