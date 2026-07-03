"""Finite-state validator for draft status transitions (TDD §2.5)."""

from __future__ import annotations

from datetime import datetime

VALID_TRANSITIONS: dict[str, set[str]] = {
    "staged": {"approved", "rejected", "snoozed"},
    "approved": {"ready_to_send"},
    "snoozed": {"staged"},
    "rejected": set(),
    "ready_to_send": set(),
}


def validate_transition(old_status: str, new_status: str) -> None:
    allowed = VALID_TRANSITIONS.get(old_status, set())
    if new_status not in allowed:
        raise ValueError(f"Invalid transition {old_status} -> {new_status}")


def validate_approve_metadata(
    new_status: str,
    approved_by: str | None,
    approved_at: datetime | None,
) -> None:
    if new_status != "approved":
        return
    if not approved_by or not approved_at:
        raise ValueError(
            "approved requires non-null approved_by and approved_at (manager identity + timestamp)"
        )
