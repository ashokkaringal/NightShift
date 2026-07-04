"""Read-only fixture enrichment for UI detail view (no new DB tables)."""

from __future__ import annotations

import json
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from api.message_format import derive_message_subject
from memory.store import get_property_display_name, get_tenant_email, resolve_property_id

FIXTURES = Path(__file__).resolve().parent.parent / "mcp" / "fixtures"

SOURCE_SENDER = {
    "email": "tenant",
    "hoa_portal": "hoa",
    "invoice": "billing",
}

# When triage has no tenant→property mapping (HOA, invoices, etc.)
ITEM_PROPERTY_LABELS: dict[str, str] = {
    "hoa-001": "Mission Flat",
    "hoa-002": "Richmond Triplex",
    "hoa-003": "Richmond Triplex",
    "invoice-invoice_001": "16th Street Fourplex",
    "invoice-invoice_002": "Valencia Condo",
    "invoice-invoice_003": "Richmond Triplex",
}


@lru_cache(maxsize=1)
def _load_all_fixtures() -> dict[str, dict]:
    merged: dict[str, dict] = {}
    inbox = FIXTURES / "inbox.json"
    if inbox.exists():
        for row in json.loads(inbox.read_text(encoding="utf-8")):
            merged[row["id"]] = row
    hoa = FIXTURES / "hoa_portal.json"
    if hoa.exists():
        for row in json.loads(hoa.read_text(encoding="utf-8")):
            merged[row["id"]] = row
    invoice_dir = FIXTURES / "invoices"
    if invoice_dir.exists():
        for txt in invoice_dir.glob("*.txt"):
            item_id = f"invoice-{txt.stem}"
            merged[item_id] = {
                "id": item_id,
                "source": "invoice",
                "tenant_id": None,
                "raw_text": txt.read_text(encoding="utf-8").strip(),
                "received_at": datetime.fromtimestamp(txt.stat().st_mtime).isoformat(),
            }
    return merged


def enrich_item(raw_item_id: str | None) -> dict:
    if not raw_item_id:
        return {}
    fixture = _load_all_fixtures().get(raw_item_id, {})
    if not fixture:
        return {
            "sender_label": _guess_sender(raw_item_id),
            "sender_email": _sender_email("email", None, raw_item_id),
            "manager_name": "Maria Santos",
        }

    source = fixture.get("source", "email")
    tenant_id = fixture.get("tenant_id")
    property_id = resolve_property_id(tenant_id) if tenant_id else None

    sender_email = _sender_email(source, tenant_id, raw_item_id)
    property_label = resolve_item_property_label(
        raw_item_id,
        property_id,
        source,
        fixture.get("raw_text"),
    )

    raw_text = fixture.get("raw_text")
    subject = derive_message_subject(raw_text, source=source)

    return {
        "sender_label": SOURCE_SENDER.get(source, _guess_sender(raw_item_id)),
        "source": source,
        "tenant_id": tenant_id,
        "tenant_email": sender_email,
        "sender_email": sender_email,
        "manager_name": "Maria Santos",
        "property_id": property_id,
        "property_label": property_label,
        "subject": subject,
        "raw_text": raw_text,
        "received_at": fixture.get("received_at"),
    }


def _sender_email(source: str, tenant_id: str | None, raw_item_id: str) -> str:
    if source == "hoa_portal":
        return "hoa@richmondheights.org"
    if source == "invoice":
        return "billing@vendor.example.com"
    if tenant_id:
        mapped = get_tenant_email(tenant_id)
        if mapped:
            return mapped
        local = tenant_id.replace("tenant-", "")
        return f"{local}@tenants.example.com"
    return f"{raw_item_id}@fixture.local"


def resolve_item_property_label(
    raw_item_id: str,
    property_id: str | None,
    source: str,
    raw_text: str | None = None,
) -> str:
    """Best display name for drafts + UI when property_id is missing or unknown."""
    mapped = get_property_display_name(property_id)
    if mapped:
        return mapped
    if raw_item_id in ITEM_PROPERTY_LABELS:
        return ITEM_PROPERTY_LABELS[raw_item_id]
    if raw_text:
        inferred = _property_from_message_text(raw_text, source)
        if inferred:
            return inferred
    if source == "hoa_portal":
        return "Richmond Triplex"
    if source == "invoice":
        return "16th Street Fourplex"
    return "Oak Street Duplex"


def _property_from_message_text(raw_text: str, source: str) -> str | None:
    text = raw_text.lower()
    if "16th street" in text or "901 16th" in text:
        return "16th Street Fourplex"
    if "unit 4b" in text or "mission hoa" in text or "mission flat" in text:
        return "Mission Flat"
    if "richmond" in text or "clement street" in text:
        return "Richmond Triplex"
    if "valencia" in text:
        return "Valencia Condo"
    if "haight" in text:
        return "Haight Cottage"
    if source == "invoice" and "no-heat" in text:
        return "Valencia Condo"
    return None


def _fallback_property_label(source: str, raw_item_id: str) -> str | None:
    if raw_item_id in ITEM_PROPERTY_LABELS:
        return ITEM_PROPERTY_LABELS[raw_item_id]
    if source == "hoa_portal":
        return "Richmond Triplex"
    if source == "invoice":
        return "16th Street Fourplex"
    return None


def _guess_sender(raw_item_id: str) -> str:
    if raw_item_id.startswith("email"):
        return "tenant"
    if raw_item_id.startswith("hoa"):
        return "hoa"
    if raw_item_id.startswith("invoice"):
        return "billing"
    return "tenant"


