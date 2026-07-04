"""Deterministic tenant → property lookup (TDD §2.3)."""

from __future__ import annotations

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"

# Demo-facing street names (used in drafts + UI detail pane)
PROPERTY_DISPLAY_NAMES: dict[str, str] = {
    "property-A": "Oak Street Duplex",
    "property-B": "Valencia Condo",
    "property-C": "Hayes Studio",
    "property-D": "Marina Unit",
    "property-E": "Noe Victorian",
    "property-F": "16th Street Fourplex",
    "property-G": "Richmond Triplex",
    "property-H": "Haight Cottage",
    "property-I": "Sunset Bungalow",
    "property-J": "Pacific Heights Flat",
}


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


def get_property_display_name(property_id: str | None) -> str | None:
    if not property_id or property_id.lower() == "unknown":
        return None
    if property_id in PROPERTY_DISPLAY_NAMES:
        return PROPERTY_DISPLAY_NAMES[property_id]
    return property_id.replace("property-", "Property ").title()


def get_tenant_email(tenant_id: str | None) -> str | None:
    if not tenant_id:
        return None
    for row in _load_json("tenant_property_map.json"):
        if row["tenant_id"] == tenant_id:
            return row.get("tenant_email")
    return None


def get_lease_dates(tenant_id: str | None) -> dict | None:
    """Return lease_start, lease_end, property_id for a tenant (deterministic lookup)."""
    if not tenant_id:
        return None
    for row in _load_json("tenant_property_map.json"):
        if row["tenant_id"] == tenant_id:
            return {
                "property_id": row["property_id"],
                "lease_start": row["lease_start"],
                "lease_end": row["lease_end"],
            }
    return None
