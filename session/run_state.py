"""Per overnight run progress — thin wrapper over RunStateStore (A2b)."""

from __future__ import annotations

from session.store import RunStateStore

# Backward-compatible alias used by SupervisorNode
RunState = RunStateStore

__all__ = ["RunState", "RunStateStore"]
