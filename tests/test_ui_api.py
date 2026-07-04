"""UI API tests — FastAPI TestClient for inbox + HITL."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from api.ui_server import app
from db.engine import SessionLocal
from db.models import DraftRow, FailedItemRow, OvernightRunRow

client = TestClient(app)


def _clear(session) -> None:
    session.query(FailedItemRow).delete()
    session.query(DraftRow).delete()
    session.query(OvernightRunRow).delete()
    session.commit()


def _seed_draft(session, **kwargs) -> DraftRow:
    defaults = dict(
        id="draft-ui-test",
        classified_item_id="classified-email-001",
        raw_item_id="email-001",
        urgency_tier="RED",
        summary="RED – water stain | Reasoning: structural",
        draft_text="We will schedule an inspection.",
        status="staged",
        approved_by=None,
        approved_at=None,
    )
    defaults.update(kwargs)
    row = DraftRow(**defaults)
    session.add(row)
    session.commit()
    return row


@pytest.fixture(autouse=True)
def clean_db():
    session = SessionLocal()
    try:
        _clear(session)
        yield
    finally:
        _clear(session)
        session.close()


def test_health() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_inbox_lists_drafts() -> None:
    session = SessionLocal()
    try:
        _seed_draft(session)
    finally:
        session.close()
    resp = client.get("/inbox?filter=inbox")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["kind"] == "draft"
    assert data[0]["urgency_tier"] == "RED"


def test_sidebar_counts() -> None:
    session = SessionLocal()
    try:
        _seed_draft(session)
        _seed_draft(
            session,
            id="draft-yellow",
            raw_item_id="email-006",
            urgency_tier="YELLOW",
            summary="YELLOW – faucet | Reasoning: follow-up",
        )
    finally:
        session.close()
    resp = client.get("/sidebar-counts")
    assert resp.status_code == 200
    counts = resp.json()
    assert counts["inbox"] >= 2
    assert counts["staged"] >= 2
    assert counts["urgent_red"] >= 1
    assert counts["yellow"] >= 1


def test_inbox_yellow_filter() -> None:
    session = SessionLocal()
    try:
        _seed_draft(session, urgency_tier="RED")
        _seed_draft(
            session,
            id="draft-yellow",
            raw_item_id="email-006",
            urgency_tier="YELLOW",
            summary="YELLOW – faucet | Reasoning: follow-up",
        )
    finally:
        session.close()
    resp = client.get("/inbox?filter=yellow")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["urgency_tier"] == "YELLOW"
    assert data[0]["raw_item_id"] == "email-006"


def test_item_detail_enriches_fixture() -> None:
    session = SessionLocal()
    try:
        _seed_draft(session)
    finally:
        session.close()
    resp = client.get("/items/draft-ui-test")
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["draft_text"]
    assert detail["property_label"] == "Oak Street Duplex"
    assert detail["raw_text"]
    assert detail["body_text"]
    assert detail["attachments"] == []
    assert detail["subject"] == "Bathroom ceiling water stain"
    assert detail["subject"] != detail["raw_text"]
    assert detail["sender_email"] == "tenant123@example.com"


def test_download_fixture_attachment() -> None:
    from pathlib import Path

    pdf = Path(__file__).resolve().parent.parent / "mcp" / "fixtures" / "attachments" / "email-009-stop-work.pdf"
    if not pdf.exists():
        pytest.skip("Run scripts/generate_pdf_fixtures.py first")

    resp = client.get("/attachments/email-009/stop-work-order.pdf")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/pdf")
    assert resp.content[:4] == b"%PDF"


def test_download_attachment_rejects_unknown_file() -> None:
    resp = client.get("/attachments/email-009/missing.pdf")
    assert resp.status_code == 404


def test_download_attachment_rejects_path_traversal() -> None:
    resp = client.get("/attachments/email-009/..%2F..%2F..%2Fetc%2Fpasswd")
    assert resp.status_code == 404


def test_item_detail_includes_pdf_attachments_for_email_007() -> None:
    from pathlib import Path

    pdf = Path(__file__).resolve().parent.parent / "mcp" / "fixtures" / "attachments" / "email-007-notice.pdf"
    if not pdf.exists():
        pytest.skip("Run scripts/generate_pdf_fixtures.py first")

    session = SessionLocal()
    try:
        _seed_draft(
            session,
            id="draft-email-007",
            classified_item_id="classified-email-007",
            raw_item_id="email-007",
            urgency_tier="RED",
            summary="RED – City code violation notice | Reasoning: code",
            draft_text="Draft pending review.",
        )
    finally:
        session.close()

    detail = client.get("/items/draft-email-007").json()
    assert detail["body_text"]
    assert "[Attachment:" not in detail["body_text"]
    assert len(detail["attachments"]) == 1
    assert detail["attachments"][0]["filename"] == "code-violation-notice.pdf"
    assert "June 27 2026" in detail["attachments"][0]["text"]
    assert "[Attachment:" in detail["raw_text"]


def test_inbox_subject_differs_from_body_snippet() -> None:
    session = SessionLocal()
    try:
        _seed_draft(session)
    finally:
        session.close()
    resp = client.get("/inbox?filter=staged")
    assert resp.status_code == 200
    item = next(i for i in resp.json() if i["raw_item_id"] == "email-001")
    assert item["subject"] == "Bathroom ceiling water stain"
    assert item["preview"] != item["subject"]


def test_approve_via_api() -> None:
    session = SessionLocal()
    try:
        _seed_draft(session)
    finally:
        session.close()
    resp = client.post("/drafts/draft-ui-test/approve", json={"manager": "Jane Doe"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"


def test_reject_via_api() -> None:
    session = SessionLocal()
    try:
        _seed_draft(session)
    finally:
        session.close()
    resp = client.post("/drafts/draft-ui-test/reject")
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"


def test_snooze_via_api() -> None:
    session = SessionLocal()
    try:
        _seed_draft(session)
    finally:
        session.close()
    resp = client.post("/drafts/draft-ui-test/snooze")
    assert resp.status_code == 200
    assert resp.json()["status"] == "snoozed"


def test_edit_approve_via_api() -> None:
    session = SessionLocal()
    try:
        _seed_draft(session)
    finally:
        session.close()
    resp = client.post(
        "/drafts/draft-ui-test/edit-approve",
        json={"manager": "Jane Doe", "text": "Manager-edited reply body."},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "approved"
    assert body["approved_by"] == "Jane Doe"
    assert body["draft_text"] == "Manager-edited reply body."


def test_save_draft_text() -> None:
    session = SessionLocal()
    try:
        _seed_draft(session)
    finally:
        session.close()
    resp = client.post(
        "/drafts/draft-ui-test/save",
        json={"text": "Updated draft body for review."},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "staged"
    detail = client.get("/items/draft-ui-test").json()
    assert detail["draft_text"] == "Updated draft body for review."


def test_green_draft_does_not_require_hitl() -> None:
    session = SessionLocal()
    try:
        _seed_draft(
            session,
            id="draft-green-test",
            classified_item_id="classified-email-002",
            raw_item_id="email-002",
            urgency_tier="GREEN",
            summary="GREEN – Lightbulb out",
            draft_text="(No tenant reply drafted — GREEN priority per NightShift policy)",
        )
    finally:
        session.close()
    resp = client.get("/items/draft-green-test")
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["requires_hitl"] is False
    assert detail["urgency_tier"] == "GREEN"


def test_approve_rejected_fails_fsm() -> None:
    session = SessionLocal()
    try:
        _seed_draft(session, status="rejected")
    finally:
        session.close()
    resp = client.post("/drafts/draft-ui-test/approve", json={"manager": "Jane Doe"})
    assert resp.status_code == 400


def test_approved_red_draft_requires_hitl_false_but_stays_approved() -> None:
    """After approve, API marks requires_hitl=False — UI must still show APPROVED, not NO REPLY."""
    session = SessionLocal()
    try:
        _seed_draft(session)
    finally:
        session.close()
    client.post("/drafts/draft-ui-test/approve", json={"manager": "Maria Santos"})
    detail = client.get("/items/draft-ui-test").json()
    assert detail["status"] == "approved"
    assert detail["requires_hitl"] is False
    assert detail["urgency_tier"] == "RED"
    assert detail["approved_by"] == "Maria Santos"
    assert not detail["draft_text"].startswith("(No tenant reply drafted")
