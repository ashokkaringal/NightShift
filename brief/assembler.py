"""Morning Brief — RED first, rationale, failed items (Member C)."""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from db.engine import SessionLocal
from db.models import DraftRow, FailedItemRow, OvernightRunRow
from models.core import UrgencyTier

TIER_ORDER: dict[str, int] = {"RED": 0, "YELLOW": 1, "GREEN": 2, "UNKNOWN": 3}


@dataclass
class BriefDraftItem:
    draft_id: str
    raw_item_id: str
    urgency_tier: str
    summary: str
    draft_text: str
    status: str


@dataclass
class BriefFailedItem:
    raw_item_id: str
    error_detail: str
    run_id: str


@dataclass
class MorningBrief:
    run_id: str | None
    drafts: list[BriefDraftItem] = field(default_factory=list)
    failed: list[BriefFailedItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "drafts": [item.__dict__ for item in self.drafts],
            "failed": [item.__dict__ for item in self.failed],
        }


def _latest_completed_run(session: Session) -> OvernightRunRow | None:
    return (
        session.query(OvernightRunRow)
        .filter(OvernightRunRow.status == "completed")
        .order_by(OvernightRunRow.finished_at.desc())
        .first()
    )


def assemble_brief(*, session: Session | None = None) -> MorningBrief:
    own = session is None
    db = session or SessionLocal()
    try:
        run = _latest_completed_run(db)
        run_id = run.id if run else None

        draft_rows = (
            db.query(DraftRow)
            .filter(DraftRow.status.in_(("staged", "snoozed")))
            .all()
        )
        draft_rows.sort(
            key=lambda r: (
                TIER_ORDER.get(r.urgency_tier or "UNKNOWN", 3),
                r.id,
            )
        )

        drafts = [
            BriefDraftItem(
                draft_id=row.id,
                raw_item_id=row.raw_item_id or row.classified_item_id.removeprefix("classified-"),
                urgency_tier=row.urgency_tier or "UNKNOWN",
                summary=row.summary or "",
                draft_text=row.draft_text,
                status=row.status,
            )
            for row in draft_rows
        ]

        failed: list[BriefFailedItem] = []
        if run_id:
            fail_rows = (
                db.query(FailedItemRow)
                .filter(FailedItemRow.run_id == run_id)
                .order_by(FailedItemRow.created_at)
                .all()
            )
            failed = [
                BriefFailedItem(
                    raw_item_id=row.raw_item_id,
                    error_detail=row.error_detail,
                    run_id=row.run_id,
                )
                for row in fail_rows
            ]

        return MorningBrief(run_id=run_id, drafts=drafts, failed=failed)
    finally:
        if own:
            db.close()


def format_brief_text(brief: MorningBrief) -> str:
    lines: list[str] = [
        "=== NightShift Morning Brief ===",
        f"Overnight run: {brief.run_id or 'none'}",
        "",
    ]

    if brief.drafts:
        lines.append("STAGED DRAFTS (RED first)")
        current_tier: UrgencyTier | str | None = None
        for item in brief.drafts:
            if item.urgency_tier != current_tier:
                current_tier = item.urgency_tier
                lines.append(f"\n[{current_tier}]")
            lines.extend(
                [
                    f"  item: {item.raw_item_id}",
                    f"  draft_id: {item.draft_id}",
                    f"  summary: {item.summary}",
                    f"  draft: {item.draft_text}",
                    f"  actions: approve | edit-approve | reject | snooze",
                    "",
                ]
            )
    else:
        lines.append("No staged drafts.")

    if brief.failed:
        lines.append("\nCOULD NOT CLASSIFY — NEEDS MANUAL REVIEW")
        for item in brief.failed:
            lines.append(f"  {item.raw_item_id}: {item.error_detail}")
    elif brief.run_id:
        lines.append("\nNo triage failures in latest run.")

    lines.append(
        "\nNightShift drafts. It never sends — phase 1 has no outbound send path; the database enforces manager approval."
    )
    return "\n".join(lines)
