"""Deterministic tenant → property lookup (TDD §2.3)."""

from __future__ import annotations

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"


def _load_json(name: str) -> list[dict]:
    path = DATA_DIR / name
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_property_id(tenant_email_or_id: str | None) -> str | None:
    if not tenant_email_or_id:
        return None
    for row in _load_json("tenant_property_map.json"):
        if row["tenant_id"] == tenant_email_or_id or row.get("tenant_email") == tenant_email_or_id:
            return row["property_id"]
    return None


def get_property_personality(property_id: str) -> str | None:
    for row in _load_json("property_personality.json"):
        if row["property_id"] == property_id:
            return row.get("note")
    return None
