"""FastAPI UI API — DraftRow + FailedItemRow for Gmail-style frontend."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.fixture_lookup import enrich_item, resolve_fixture_attachment_path
from api.message_format import derive_message_subject, message_snippet
from db.engine import SessionLocal
from db.models import DraftRow, FailedItemRow, OvernightRunRow
from hitl.actions import approve_draft, edit_and_approve, reject_draft, save_draft_text, snooze_draft

app = FastAPI(title="NightShift UI API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TIER_ORDER = {"RED": 0, "YELLOW": 1, "GREEN": 2, "SPAM": 3, "UNKNOWN": 4}
NO_REPLY_DRAFT_PREFIX = "(No tenant reply drafted"


class ApproveBody(BaseModel):
    manager: str = Field(min_length=1)


class EditApproveBody(BaseModel):
    manager: str = Field(min_length=1)
    text: str = Field(min_length=1)


class SaveDraftBody(BaseModel):
    text: str = Field(min_length=1)


class InboxItem(BaseModel):
    id: str
    kind: str
    raw_item_id: str
    sender_label: str
    subject: str
    preview: str
    urgency_tier: str | None = None
    status: str | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    display_time: str | None = None
    run_id: str | None = None
    error_detail: str | None = None


class AttachmentDetail(BaseModel):
    filename: str
    text: str
    kind: str = "pdf"


class InboxDetail(InboxItem):
    draft_text: str | None = None
    draft_text_alt: str | None = None
    summary: str | None = None
    reasoning: str | None = None
    tenant_email: str | None = None
    sender_email: str | None = None
    manager_name: str | None = None
    property_label: str | None = None
    raw_text: str | None = None
    body_text: str | None = None
    attachments: list[AttachmentDetail] = Field(default_factory=list)
    received_at: str | None = None
    requires_hitl: bool = True


def _requires_hitl(row: DraftRow) -> bool:
    if row.urgency_tier in ("GREEN", "SPAM"):
        return False
    if (row.draft_text or "").startswith(NO_REPLY_DRAFT_PREFIX):
        return False
    return row.status in ("staged", "snoozed")


class SidebarCounts(BaseModel):
    inbox: int
    staged: int
    urgent_red: int
    yellow: int
    spam: int
    spam_unread: int
    approved: int
    snoozed: int
    rejected: int


class OvernightRunOption(BaseModel):
    id: str
    label: str
    message_count: int


def _session() -> Session:
    return SessionLocal()


def _parse_subject(summary: str | None) -> tuple[str, str]:
    if not summary:
        return "Overnight item", ""
    if "| Reasoning:" in summary:
        main, _, reasoning = summary.partition("| Reasoning:")
        subject = main.split("–", 1)[-1].strip() if "–" in main else main.strip()
        return subject[:80] or "Overnight item", reasoning.strip()
    parts = summary.split("–", 1)
    subject = parts[-1].strip() if parts else summary
    return subject[:80] or "Overnight item", ""


def _parse_datetime(value: datetime | str | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _format_display_datetime(value: datetime | str | None) -> str | None:
    parsed = _parse_datetime(value)
    if parsed is None:
        return None
    return parsed.strftime("%b %d, %Y, %H:%M")


def _draft_to_item(row: DraftRow) -> InboxItem:
    enrich = enrich_item(row.raw_item_id)
    raw_text = enrich.get("raw_text")
    body_text = enrich.get("body_text") or raw_text
    subject = enrich.get("subject") or derive_message_subject(body_text)
    preview = message_snippet(body_text) or row.summary or subject
    display_time = _format_display_datetime(row.approved_at) or _format_display_datetime(
        enrich.get("received_at")
    )
    return InboxItem(
        id=row.id,
        kind="draft",
        raw_item_id=row.raw_item_id or row.id,
        sender_label=enrich.get("sender_label", "tenant"),
        subject=subject,
        preview=preview,
        urgency_tier=row.urgency_tier,
        status=row.status,
        approved_by=row.approved_by,
        approved_at=row.approved_at,
        display_time=display_time,
    )


def _failed_to_item(row: FailedItemRow) -> InboxItem:
    enrich = enrich_item(row.raw_item_id)
    return InboxItem(
        id=row.id,
        kind="failed",
        raw_item_id=row.raw_item_id,
        sender_label=enrich.get("sender_label", "tenant"),
        subject=f"Failed: {row.raw_item_id}",
        preview=row.error_detail[:120],
        urgency_tier=None,
        status="failed",
        display_time=_format_display_datetime(row.created_at),
        run_id=row.run_id,
        error_detail=row.error_detail,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/sidebar-counts", response_model=SidebarCounts)
def sidebar_counts(run_id: str | None = None) -> SidebarCounts:
    db = _session()
    try:
        drafts = _query_drafts(db, run_id=run_id)
        failed = _query_failed(db, run_id=run_id)
        spam = sum(1 for d in drafts if d.urgency_tier == "SPAM")
        spam_unread = sum(1 for d in drafts if d.urgency_tier == "SPAM" and d.read_at is None)
        return SidebarCounts(
            inbox=(len(drafts) - spam) + len(failed),
            staged=sum(1 for d in drafts if d.status == "staged" and d.urgency_tier != "SPAM"),
            urgent_red=sum(1 for d in drafts if d.urgency_tier == "RED"),
            yellow=sum(1 for d in drafts if d.urgency_tier == "YELLOW"),
            spam=spam,
            spam_unread=spam_unread,
            approved=sum(1 for d in drafts if d.status == "approved"),
            snoozed=sum(1 for d in drafts if d.status == "snoozed"),
            rejected=sum(1 for d in drafts if d.status == "rejected"),
        )
    finally:
        db.close()


@app.get("/overnight-runs", response_model=list[OvernightRunOption])
def overnight_runs() -> list[OvernightRunOption]:
    db = _session()
    try:
        runs = (
            db.query(OvernightRunRow)
            .order_by(OvernightRunRow.finished_at.desc().nullslast())
            .all()
        )
        options: list[OvernightRunOption] = []
        for run in runs:
            failed_n = db.query(FailedItemRow).filter(FailedItemRow.run_id == run.id).count()
            count = run.processed + failed_n
            finished = run.finished_at.strftime("%Y-%m-%d") if run.finished_at else run.id
            options.append(
                OvernightRunOption(
                    id=run.id,
                    label=f"{finished}-demo ({count} msgs)",
                    message_count=count,
                )
            )
        if not options:
            options.append(OvernightRunOption(id="local", label="local-demo (0 msgs)", message_count=0))
        return options
    finally:
        db.close()


def _query_drafts(db: Session, *, run_id: str | None, urgency: str | None = None, status: str | None = None) -> list[DraftRow]:
    q = db.query(DraftRow)
    if urgency:
        q = q.filter(DraftRow.urgency_tier == urgency)
    if status:
        q = q.filter(DraftRow.status == status)
    rows = q.all()
    rows.sort(key=lambda r: (TIER_ORDER.get(r.urgency_tier or "UNKNOWN", 3), r.id))
    return rows


def _query_failed(db: Session, *, run_id: str | None) -> list[FailedItemRow]:
    q = db.query(FailedItemRow)
    if run_id and run_id != "local":
        q = q.filter(FailedItemRow.run_id == run_id)
    return q.order_by(FailedItemRow.created_at.desc()).all()


@app.get("/inbox", response_model=list[InboxItem])
def inbox(
    filter: str = Query("inbox", alias="filter"),
    run_id: str | None = None,
    q: str | None = None,
) -> list[InboxItem]:
    db = _session()
    try:
        urgency = status = None
        if filter == "staged":
            status = "staged"
        elif filter == "urgent":
            urgency = "RED"
        elif filter == "yellow":
            urgency = "YELLOW"
        elif filter == "spam":
            urgency = "SPAM"
        elif filter == "approved":
            status = "approved"
        elif filter == "snoozed":
            status = "snoozed"
        elif filter == "rejected":
            status = "rejected"

        items: list[InboxItem] = []
        if filter != "failed":
            drafts = _query_drafts(db, run_id=run_id, urgency=urgency, status=status)
            if filter != "spam":
                drafts = [r for r in drafts if r.urgency_tier != "SPAM"]
            items.extend(_draft_to_item(r) for r in drafts)
        if filter in ("inbox", "failed"):
            items.extend(_failed_to_item(r) for r in _query_failed(db, run_id=run_id))

        if filter == "inbox":
            items.sort(
                key=lambda i: (
                    0 if i.kind == "draft" else 1,
                    TIER_ORDER.get(i.urgency_tier or "UNKNOWN", 3),
                    i.id,
                )
            )

        if q:
            needle = q.lower()
            items = [
                i
                for i in items
                if needle in i.subject.lower()
                or needle in i.preview.lower()
                or needle in i.sender_label.lower()
                or needle in i.raw_item_id.lower()
            ]
        return items
    finally:
        db.close()


@app.get("/items/{item_id}", response_model=InboxDetail)
def item_detail(item_id: str) -> InboxDetail:
    db = _session()
    try:
        row = db.get(DraftRow, item_id)
        if row is None:
            row = db.query(DraftRow).filter(DraftRow.raw_item_id == item_id).first()
        if row is not None:
            base = _draft_to_item(row)
            _, reasoning = _parse_subject(row.summary)
            enrich = enrich_item(row.raw_item_id)
            payload = base.model_dump()
            payload["subject"] = enrich.get("subject") or base.subject
            return InboxDetail(
                **payload,
                draft_text=row.draft_text,
                draft_text_alt=row.draft_text_alt,
                summary=row.summary,
                reasoning=reasoning or None,
                tenant_email=enrich.get("tenant_email"),
                sender_email=enrich.get("sender_email"),
                manager_name=enrich.get("manager_name"),
                property_label=enrich.get("property_label"),
                raw_text=enrich.get("raw_text"),
                body_text=enrich.get("body_text"),
                attachments=enrich.get("attachments") or [],
                received_at=enrich.get("received_at"),
                requires_hitl=_requires_hitl(row),
            )

        failed = db.get(FailedItemRow, item_id)
        if failed is None:
            failed = db.query(FailedItemRow).filter(FailedItemRow.raw_item_id == item_id).first()
        if failed is not None:
            base = _failed_to_item(failed)
            enrich = enrich_item(failed.raw_item_id)
            return InboxDetail(
                **base.model_dump(),
                raw_text=enrich.get("raw_text"),
                body_text=enrich.get("body_text"),
                attachments=enrich.get("attachments") or [],
                received_at=enrich.get("received_at"),
                property_label=enrich.get("property_label"),
                tenant_email=enrich.get("tenant_email"),
                sender_email=enrich.get("sender_email"),
                manager_name=enrich.get("manager_name"),
                requires_hitl=False,
            )

        raise HTTPException(status_code=404, detail=f"Item not found: {item_id}")
    finally:
        db.close()


@app.get("/attachments/{raw_item_id}/{filename}")
def download_attachment(raw_item_id: str, filename: str) -> FileResponse:
    """Read-only fixture PDF download — only registered inbox attachments."""
    safe_name = Path(unquote(filename)).name
    path = resolve_fixture_attachment_path(raw_item_id, safe_name)
    if path is None:
        raise HTTPException(status_code=404, detail=f"Attachment not found: {safe_name}")
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=safe_name,
    )


@app.post("/drafts/{draft_id}/mark-read")
def api_mark_read(draft_id: str) -> dict:
    db = _session()
    try:
        row = db.get(DraftRow, draft_id)
        if row is None:
            raise HTTPException(status_code=404, detail=f"Draft not found: {draft_id}")
        if row.urgency_tier != "SPAM":
            raise HTTPException(status_code=400, detail="Only spam drafts can be marked read")
        if row.read_at is None:
            row.read_at = datetime.now(timezone.utc)
            db.commit()
        return {"id": row.id, "read_at": row.read_at.isoformat() if row.read_at else None}
    finally:
        db.close()


@app.post("/drafts/{draft_id}/approve")
def api_approve(draft_id: str, body: ApproveBody) -> dict:
    try:
        draft = approve_draft(draft_id, body.manager)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"id": draft.id, "status": draft.status, "approved_by": draft.approved_by}


@app.post("/drafts/{draft_id}/reject")
def api_reject(draft_id: str) -> dict:
    try:
        draft = reject_draft(draft_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"id": draft.id, "status": draft.status}


@app.post("/drafts/{draft_id}/snooze")
def api_snooze(draft_id: str) -> dict:
    try:
        draft = snooze_draft(draft_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"id": draft.id, "status": draft.status}


@app.post("/drafts/{draft_id}/edit-approve")
def api_edit_approve(draft_id: str, body: EditApproveBody) -> dict:
    try:
        draft = edit_and_approve(draft_id, body.manager, body.text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "id": draft.id,
        "status": draft.status,
        "draft_text": draft.draft_text,
        "approved_by": draft.approved_by,
    }


@app.post("/drafts/{draft_id}/save")
def api_save_draft(draft_id: str, body: SaveDraftBody) -> dict:
    try:
        draft = save_draft_text(draft_id, body.text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"id": draft.id, "status": draft.status, "draft_text": draft.draft_text}
