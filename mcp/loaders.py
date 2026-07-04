"""MCP read tool implementations — shared by server and direct ingestion."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from mcp.pdf_parser import (
    extract_pdf_text,
    format_attachment_block,
    resolve_attachment_path,
)
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


def load_attachments_from_row(row: dict, *, fixtures_root: Path = FIXTURES) -> list[dict[str, str]]:
    """Extract PDF attachment text from an inbox fixture row."""
    attachments = row.get("attachments") or []
    if not attachments:
        return []
    result: list[dict[str, str]] = []
    for att in attachments:
        rel = att.get("path") or att.get("filename") or ""
        filename = att.get("filename") or Path(rel).name
        pdf_path = resolve_attachment_path(fixtures_root, rel)
        extracted = extract_pdf_text(pdf_path)
        result.append(
            {
                "filename": filename,
                "text": extracted.text,
                "kind": "pdf",
            }
        )
    return result


def _append_attachment_text(body: str, row: dict) -> str:
    """Merge optional PDF attachment text into email body."""
    att_list = load_attachments_from_row(row)
    if not att_list:
        return body
    parts = [body]
    for att in att_list:
        parts.append(format_attachment_block(att["filename"], att["text"]))
    return "".join(parts)


def _inbox_row_to_item(row: dict) -> RawItem:
    raw_text = _append_attachment_text(row["raw_text"], row)
    return RawItem(
        id=row["id"],
        source=row["source"],
        tenant_id=row.get("tenant_id"),
        raw_text=raw_text,
        received_at=_parse_dt(row["received_at"]),
    )


def read_inbox(since: datetime | None = None, *, token: str | None = DEV_TOKEN) -> list[RawItem]:
    """read_inbox(since: datetime | None) → list[RawItem]

    Returns overnight email items newer than `since` (UTC). Bearer token required.
    Optional fixture attachments (PDF) are extracted into raw_text.
    Mock backing: mcp/fixtures/inbox.json.
    """
    _authorize(token)
    path = FIXTURES / "inbox.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    items = [_inbox_row_to_item(row) for row in data]
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


def _invoice_item_from_path(path: Path) -> RawItem:
    if path.suffix.lower() == ".pdf":
        result = extract_pdf_text(path)
        body = result.text.strip() or "\n".join(result.warnings)
    else:
        body = path.read_text(encoding="utf-8").strip()
    return RawItem(
        id=f"invoice-{path.stem}",
        source="invoice",
        tenant_id=None,
        raw_text=body,
        received_at=datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc),
    )


def read_invoices_folder(*, token: str | None = DEV_TOKEN) -> list[RawItem]:
    """read_invoices_folder() → list[RawItem]

    Returns one RawItem per invoice in mcp/fixtures/invoices/*.txt or *.pdf.
    Bearer token required. Raises PermissionError if token is invalid.
    """
    _authorize(token)
    invoice_dir = FIXTURES / "invoices"
    if not invoice_dir.exists():
        return []
    seen_stems: set[str] = set()
    items: list[RawItem] = []
    # Prefer .txt when both exist for the same stem (backward compatible fixtures).
    for path in sorted(invoice_dir.glob("*")):
        if path.suffix.lower() not in {".txt", ".pdf"}:
            continue
        if path.stem in seen_stems:
            continue
        txt_alt = path.with_suffix(".txt")
        pdf_alt = path.with_suffix(".pdf")
        if path.suffix.lower() == ".pdf" and txt_alt.exists():
            continue
        if path.suffix.lower() == ".txt" and pdf_alt.exists():
            seen_stems.add(path.stem)
            items.append(_invoice_item_from_path(path))
            continue
        seen_stems.add(path.stem)
        items.append(_invoice_item_from_path(path))
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
