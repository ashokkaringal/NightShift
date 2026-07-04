"""Executable Gherkin specs — Member B (B6)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from agents.triage.agent import TriageAgent
from db.fsm import validate_approve_metadata, validate_transition
from policy.check_no_send import check_no_send
from tests.eval_urgency import load_labeled_cases

scenarios("../features/urgency_classification.feature")
scenarios("../features/hitl_state_machine.feature")


@pytest.fixture
def bdd_context() -> dict:
    return {}


@given(parsers.parse('an inbox item with id "{item_id}"'))
def inbox_item(bdd_context: dict, item_id: str) -> None:
    case = next((c for c in load_labeled_cases() if c.id == item_id), None)
    assert case is not None, f"Unknown fixture id: {item_id}"
    bdd_context["raw_item"] = case.item


@when("TriageAgent classifies the item")
def classify_item(bdd_context: dict) -> None:
    bdd_context["classified"] = TriageAgent().run(bdd_context["raw_item"])


@then(parsers.parse('urgency tier should be "{tier}"'))
def assert_urgency_tier(bdd_context: dict, tier: str) -> None:
    assert bdd_context["classified"].urgency_tier == tier


@given(parsers.parse('a draft in status "{status}"'))
def draft_status(bdd_context: dict, status: str) -> None:
    bdd_context["status"] = status


@when(parsers.parse('manager attempts transition to "{target}"'))
def attempt_transition(bdd_context: dict, target: str) -> None:
    bdd_context["error"] = None
    try:
        check_no_send(bdd_context["status"], target)
        validate_transition(bdd_context["status"], target)
    except ValueError as exc:
        bdd_context["error"] = exc


@when(parsers.parse('manager approves with name "{manager}"'))
def approve_draft(bdd_context: dict, manager: str) -> None:
    bdd_context["error"] = None
    try:
        validate_transition(bdd_context["status"], "approved")
        validate_approve_metadata("approved", manager, datetime.now(timezone.utc))
        bdd_context["status"] = "approved"
    except ValueError as exc:
        bdd_context["error"] = exc


@then("transition should be rejected")
def transition_rejected(bdd_context: dict) -> None:
    assert bdd_context.get("error") is not None


@then(parsers.parse('status should be "{status}"'))
def assert_status(bdd_context: dict, status: str) -> None:
    assert bdd_context.get("error") is None
    assert bdd_context["status"] == status
