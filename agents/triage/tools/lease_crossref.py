"""Lease schedule cross-reference — restricted sandbox placeholder (TDD §2.8)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime

from memory.store import get_lease_dates

_DATE_PATTERNS = (
    re.compile(r"\b(\d{4}-\d{2}-\d{2})\b"),
    re.compile(
        r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bby\s+(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b", re.IGNORECASE),
)


def _parse_notice_date(text: str, received_at: datetime) -> date | None:
    iso = _DATE_PATTERNS[0].search(text)
    if iso:
        return date.fromisoformat(iso.group(1))

    month_day = _DATE_PATTERNS[1].search(text)
    if month_day:
        month_name, day = month_day.group(1), int(month_day.group(2))
        month = datetime.strptime(month_name[:3], "%b").month
        return date(received_at.year, month, day)

    if _DATE_PATTERNS[2].search(text):
        return received_at.date()

    return received_at.date()


@dataclass(frozen=True)
class LeaseCrossRefResult:
    tenant_id: str
    property_id: str | None
    notice_date: date
    lease_start: date
    lease_end: date
    lease_covers_notice: bool

    def summary_line(self) -> str:
        status = "active lease covers notice date" if self.lease_covers_notice else "notice date outside lease term"
        return (
            f"Lease cross-ref ({self.tenant_id}): {status} "
            f"({self.lease_start.isoformat()} – {self.lease_end.isoformat()}, notice {self.notice_date.isoformat()})"
        )


def cross_reference_notice(
    tenant_id: str | None,
    notice_text: str,
    received_at: datetime,
) -> LeaseCrossRefResult | None:
    """Cross-reference a notice date against the tenant lease window."""
    if not tenant_id:
        return None

    lease = get_lease_dates(tenant_id)
    if lease is None:
        return None

    notice_date = _parse_notice_date(notice_text, received_at)
    lease_start = date.fromisoformat(lease["lease_start"])
    lease_end = date.fromisoformat(lease["lease_end"])
    covers = lease_start <= notice_date <= lease_end

    return LeaseCrossRefResult(
        tenant_id=tenant_id,
        property_id=lease.get("property_id"),
        notice_date=notice_date,
        lease_start=lease_start,
        lease_end=lease_end,
        lease_covers_notice=covers,
    )
