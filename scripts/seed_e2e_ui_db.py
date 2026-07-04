"""Deterministic SQLite seed for Playwright UI regression tests."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

db_path = ROOT / "ui_e2e.db"
os.environ["DB_URL"] = f"sqlite:///{db_path}"

from sqlalchemy.orm import Session

from db.engine import engine
from db.init_db import init_db
from db.models import DraftRow, OvernightRunRow


def seed() -> None:
    if db_path.exists():
        db_path.unlink()

    init_db()
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    session = Session(bind=engine)
    try:
        session.add(
            OvernightRunRow(
                id="e2e-run",
                status="completed",
                processed=5,
                failed=0,
                started_at=now,
                finished_at=now,
            )
        )

        session.add_all(
            [
                DraftRow(
                    id="draft-e2e-approved",
                    classified_item_id="classified-email-001",
                    raw_item_id="email-001",
                    urgency_tier="RED",
                    summary="RED – water stain | Reasoning: structural",
                    draft_text=(
                        "Hi, Thank you for reaching out about the bathroom ceiling water stain "
                        "at Oak Street Duplex. This issue is flagged as urgent."
                    ),
                    status="approved",
                    approved_by="Maria Santos",
                    approved_at=now,
                ),
                DraftRow(
                    id="draft-e2e-yellow",
                    classified_item_id="classified-email-006",
                    raw_item_id="email-006",
                    urgency_tier="YELLOW",
                    summary="YELLOW – faucet | Reasoning: follow-up",
                    draft_text=(
                        "Hi,\n\nThank you for reaching out about the drippy faucet follow-up "
                        "at Valencia Condo."
                    ),
                    status="staged",
                ),
                DraftRow(
                    id="draft-e2e-green",
                    classified_item_id="classified-email-002",
                    raw_item_id="email-002",
                    urgency_tier="GREEN",
                    summary="GREEN – lightbulb",
                    draft_text="(No tenant reply drafted — GREEN priority per NightShift policy)",
                    status="staged",
                ),
                DraftRow(
                    id="draft-e2e-rejected",
                    classified_item_id="classified-email-003",
                    raw_item_id="email-003",
                    urgency_tier="RED",
                    summary="RED – no heat | Reasoning: habitability",
                    draft_text=(
                        "Hi, Thank you for reaching out about the no heat in unit 4B at Valencia Condo."
                    ),
                    status="rejected",
                ),
                DraftRow(
                    id="draft-e2e-staged",
                    classified_item_id="classified-email-007",
                    raw_item_id="email-007",
                    urgency_tier="RED",
                    summary="RED – code violation | Reasoning: compliance",
                    draft_text=(
                        "Hi, Thank you for the city code violation notice. "
                        "We will address the railing repair by Friday."
                    ),
                    status="staged",
                ),
            ]
        )
        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    seed()
    print(f"E2E UI database seeded at {db_path}")
