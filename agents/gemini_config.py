"""Shared Gemini env flags — independent triage/draft stubs + token-saving live subset."""

from __future__ import annotations

import os


def _truthy(name: str) -> bool:
    return os.getenv(name, "").lower() in {"1", "true", "yes"}


def has_api_key() -> bool:
    return bool(os.getenv("GEMINI_API_KEY"))


def live_only_ids() -> frozenset[str] | None:
    """When set, only these raw_item_ids call Gemini; others use rules/templates."""
    raw = os.getenv("GEMINI_LIVE_ONLY_IDS", "").strip()
    if not raw:
        return None
    return frozenset(part.strip() for part in raw.split(",") if part.strip())


def in_live_subset(raw_item_id: str | None) -> bool:
    subset = live_only_ids()
    if subset is None:
        return True
    return bool(raw_item_id and raw_item_id in subset)
