"""Tests for Gmail-style subject/snippet formatting."""

from __future__ import annotations

from api.message_format import derive_message_subject, message_snippet


def test_water_stain_subject_is_short_not_full_body() -> None:
    body = (
        "The ceiling above my bathroom has a small water stain, has had it for a week, "
        "nothing dripping yet."
    )
    subject = derive_message_subject(body)
    assert subject == "Bathroom ceiling water stain"
    assert subject != body
    assert len(subject) < len(body)


def test_city_violation_subject() -> None:
    body = "City code violation notice scanned copy attached — says exterior stairs need railing repair by Friday."
    assert derive_message_subject(body) == "City code violation notice"


def test_drippy_faucet_subject_is_email_006() -> None:
    body = "Can you confirm you recieved my maintanance request from last week about the drippy faucet?"
    assert derive_message_subject(body) == "Drippy faucet follow-up"


def test_snippet_truncates_long_body() -> None:
    body = "A" * 200
    snippet = message_snippet(body, max_len=50)
    assert len(snippet) <= 50
    assert snippet.endswith("...")
