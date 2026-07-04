"""Member A sandbox tool tests — invoice audit + lease cross-reference."""

from __future__ import annotations

from datetime import datetime, timezone

from agents.triage.tools.invoice_audit import audit_invoice_text
from agents.triage.tools.lease_crossref import cross_reference_notice
from memory.store import get_lease_dates


def test_invoice_audit_detects_mismatch() -> None:
    text = (
        "Invoice #8842 — Bright Spark Electric\n"
        "Line items: labor $120.00, materials $45.00\n"
        "Stated total: $200.00"
    )
    result = audit_invoice_text(text)
    assert result.computed_total == 165.0
    assert result.stated_total == 200.0
    assert result.mismatch is True
    assert result.delta == 35.0


def test_invoice_audit_passes_when_totals_match() -> None:
    text = "Fee: $95.00\nStated total: $95.00"
    result = audit_invoice_text(text)
    assert result.computed_total == 95.0
    assert result.mismatch is False


def test_lease_crossref_active_tenant() -> None:
    received = datetime(2026, 6, 29, 23, 15, tzinfo=timezone.utc)
    result = cross_reference_notice(
        "tenant-123",
        "City code violation notice — repair exterior stairs by Friday.",
        received,
    )
    assert result is not None
    assert result.lease_covers_notice is True
    assert result.property_id == "property-A"


def test_get_lease_dates_from_memory() -> None:
    lease = get_lease_dates("tenant-456")
    assert lease is not None
    assert lease["lease_start"] == "2025-06-01"
    assert lease["property_id"] == "property-B"
