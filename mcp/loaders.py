"""MCP read tool implementations — shared by server and direct ingestion."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from models.core import RawItem

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures"
DEV_TOKEN = os.getenv("MCP_SERVICE_TOKEN", "dev-token-placeholder")


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _authorize(token: str | None) -> None:
    if token != DEV_TOKEN:
        raise PermissionError("Invalid MCP bearer token")


def _filter_since(items: list[RawItem], since: datetime | None) -> list[RawItem]:
    if since is None:
        return items
    return [item for item in items if item.received_at >= since]


def read_inbox(since: datetime | None = None, *, token: str | None = DEV_TOKEN) -> list[RawItem]:
    """read_inbox(since: datetime | None) → list[RawItem]

    Returns overnight email items newer than `since` (UTC). Bearer token required.
  Raises PermissionError if token is invalid. Mock backing: mcp/fixtures/inbox.json.
    """
    _authorize(token)
    path = FIXTURES / "inbox.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    items = [RawItem(**row) for row in data]
    return _filter_since(items, since)


def read_hoa_portal(since: datetime | None = None, *, token: str | None = DEV_TOKEN) -> list[RawItem]:
    """read_hoa_portal(since: datetime | None) → list[RawItem]

    Returns HOA portal notices newer than `since`. Bearer token required.
    Raises PermissionError if token is invalid. Mock: mcp/fixtures/hoa_portal.json.
    """
    _authorize(token)
    path = FIXTURES / "hoa_portal.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    items = [RawItem(**row) for row in data]
    return _filter_since(items, since)


def read_invoices_folder(*, token: str | None = DEV_TOKEN) -> list[RawItem]:
    """read_invoices_folder() → list[RawItem]

    Returns one RawItem per invoice text file in mcp/fixtures/invoices/*.txt.
    Bearer token required. Raises PermissionError if token is invalid.
    """
    _authorize(token)
    invoice_dir = FIXTURES / "invoices"
    if not invoice_dir.exists():
        return []
    items: list[RawItem] = []
    for txt in sorted(invoice_dir.glob("*.txt")):
        body = txt.read_text(encoding="utf-8").strip()
        items.append(
            RawItem(
                id=f"invoice-{txt.stem}",
                source="invoice",
                tenant_id=None,
                raw_text=body,
                received_at=datetime.fromtimestamp(txt.stat().st_mtime, tz=timezone.utc),
            )
        )
    return items


def ingest_all_sources(since: datetime | None = None, *, token: str | None = DEV_TOKEN) -> list[RawItem]:
    """Merge all three MCP read tools; dedupe by id."""
    merged: dict[str, RawItem] = {}
    for item in (
        read_inbox(since, token=token)
        + read_hoa_portal(since, token=token)
        + read_invoices_folder(token=token)
    ):
        merged[item.id] = item
    return sorted(merged.values(), key=lambda i: i.received_at)
