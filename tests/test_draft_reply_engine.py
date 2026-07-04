"""Tests for rules-first draft reply engine."""

from __future__ import annotations

from agents.response.agent import build_draft_text
from agents.response.draft_reply_engine import DraftInput, generate_draft_reply
from models.core import ClassifiedItem
from datetime import datetime, timezone


def test_red_city_template_matches_demo_copy() -> None:
    out = generate_draft_reply(
        DraftInput(
            urgency="RED",
            source_type="city",
            property_display_name="Oak Street Duplex",
            issue_subject="City code violation notice",
        )
    )
    assert out.template_id == "red_city_v1"
    assert "city code violation notice at oak street duplex" in out.body.lower()
    assert "stop-work order" in out.body
    assert "— Maria Santos" in out.body


def test_red_gas_template() -> None:
    out = generate_draft_reply(
        DraftInput(
            urgency="RED",
            source_type="tenant",
            property_display_name="Valencia Condo",
            show_911_banner=True,
        )
    )
    assert out.template_id == "red_gas_v1"
    assert "911" in out.body


def test_yellow_template() -> None:
    out = generate_draft_reply(
        DraftInput(urgency="YELLOW", source_type="tenant", property_display_name="Haight Cottage")
    )
    assert out.template_id == "yellow_ack_v1"
    assert "1–2 business days" in out.body


def test_green_returns_no_draft() -> None:
    out = generate_draft_reply(
        DraftInput(urgency="GREEN", source_type="tenant", property_display_name="16th Street Fourplex")
    )
    assert out.status == "NO_DRAFT"
    assert out.body is None


def test_email_007_uses_city_template() -> None:
    classified = ClassifiedItem(
        id="classified-email-007",
        raw_item_id="email-007",
        urgency_tier="RED",
        property_id="property-A",
        summary="RED – City code violation notice | Reasoning: code",
        classified_at=datetime.now(timezone.utc),
    )
    text, template = build_draft_text(classified)
    assert "stop-work order" in text
    assert "city code violation notice at oak street duplex" in text.lower()
    assert "Unknown" not in text


def test_email_001_draft_matches_subject_topic() -> None:
    classified = ClassifiedItem(
        id="classified-email-001",
        raw_item_id="email-001",
        urgency_tier="RED",
        property_id="property-A",
        summary="RED – water stain | Reasoning: structural",
        classified_at=datetime.now(timezone.utc),
    )
    text, _ = build_draft_text(classified)
    assert "bathroom ceiling water stain at oak street duplex" in text.lower()
    assert "Thank you for reaching out regarding Oak Street Duplex" not in text


def test_hoa_item_uses_building_name_not_unknown() -> None:
    classified = ClassifiedItem(
        id="classified-hoa-003",
        raw_item_id="hoa-003",
        urgency_tier="RED",
        property_id="unknown",
        summary="RED – Fire alarm inspection | Reasoning: safety",
        classified_at=datetime.now(timezone.utc),
    )
    text, _ = build_draft_text(classified)
    assert "Richmond Triplex" in text
    assert "Unknown" not in text


def test_invoice_item_uses_property_name() -> None:
    classified = ClassifiedItem(
        id="classified-invoice-invoice_001",
        raw_item_id="invoice-invoice_001",
        urgency_tier="YELLOW",
        property_id="unknown",
        summary="YELLOW – Invoice panel inspection | Reasoning: financial",
        classified_at=datetime.now(timezone.utc),
    )
    text, _ = build_draft_text(classified)
    assert "16th Street Fourplex" in text
    assert "Unknown" not in text
