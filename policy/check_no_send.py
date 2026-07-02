"""Policy: NightShift drafts. It never sends — enforced at code + DB layer."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db.fsm import validate_transition


def check_no_send(current_status: str, target_status: str) -> None:
    """
    Raise ValueError if transition would bypass human approval.
    Called before any outbound send path (Day 4 security pillar).
    """
    if target_status == "ready_to_send":
        raise ValueError(
            "NightShift never auto-sends: staged → ready_to_send is forbidden. "
            "Use staged → approved → sent."
        )
    validate_transition(current_status, target_status)


if __name__ == "__main__":
    try:
        check_no_send("staged", "ready_to_send")
    except ValueError as exc:
        print(f"PASS: {exc}")
    else:
        raise SystemExit("FAIL: staged → ready_to_send should be blocked")
