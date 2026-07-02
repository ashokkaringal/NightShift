"""Finite-state validator for draft status transitions (TDD §2.5)."""

from __future__ import annotations

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
