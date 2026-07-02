"""Shared Pydantic contracts — single import source for all agents (TDD §2.2.1)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

SourceType = Literal["email", "hoa_portal", "invoice"]
UrgencyTier = Literal["RED", "YELLOW", "GREEN"]
DraftStatus = Literal["staged", "approved", "rejected", "snoozed", "ready_to_send"]


class RawItem(BaseModel):
    id: str
    source: SourceType
    tenant_id: str | None = None
    raw_text: str
    received_at: datetime


class ClassifiedItem(BaseModel):
    id: str
    raw_item_id: str
    urgency_tier: UrgencyTier
    property_id: str
    summary: str
    classified_at: datetime


class Draft(BaseModel):
    id: str
    classified_item_id: str
    draft_text: str
    status: DraftStatus = "staged"
    approved_by: str | None = None
    approved_at: datetime | None = None
