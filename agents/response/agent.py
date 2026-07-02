"""ResponseAgent — Day 1 stub drafts to staged DB."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from db.models import DraftRow
from memory.store import get_property_personality
from models.core import ClassifiedItem, Draft


class ResponseAgent:
    name = "ResponseAgent"

    def run(self, classified: ClassifiedItem, session: Session) -> Draft:
        personality = get_property_personality(classified.property_id) or ""
        draft_text = (
            f"[STUB DRAFT] Acknowledging {classified.urgency_tier} item for "
            f"{classified.property_id}. {personality}"
        ).strip()

        draft = Draft(
            id=f"draft-{classified.id}",
            classified_item_id=classified.id,
            draft_text=draft_text,
            status="staged",
            approved_by=None,
            approved_at=None,
        )

        row = DraftRow(
            id=draft.id,
            classified_item_id=draft.classified_item_id,
            draft_text=draft.draft_text,
            status=draft.status,
            approved_by=draft.approved_by,
            approved_at=draft.approved_at,
        )
        session.add(row)
        session.commit()
        return draft
