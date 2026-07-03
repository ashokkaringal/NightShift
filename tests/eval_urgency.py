"""Urgency eval harness — confusion matrix + hard-case regression (Member B)."""

from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path

import pytest

from agents.triage.agent import TriageAgent
from models.core import RawItem, UrgencyTier

FIXTURES = Path(__file__).parent / "fixtures" / "eval_urgency_labeled.json"
TIERS: tuple[UrgencyTier, ...] = ("RED", "YELLOW", "GREEN")


class LabeledCase:
    def __init__(self, row: dict) -> None:
        self.expected: UrgencyTier = row.pop("expected_urgency_tier")
        self.item = RawItem.model_validate(row)
        self.id = self.item.id


def load_labeled_cases() -> list[LabeledCase]:
    data = json.loads(FIXTURES.read_text(encoding="utf-8"))
    return [LabeledCase(dict(row)) for row in data]


def confusion_matrix(
    cases: list[LabeledCase],
    agent: TriageAgent | None = None,
) -> tuple[dict[tuple[str, str], int], list[dict]]:
    triage = agent or TriageAgent()
    matrix: Counter[tuple[str, str]] = Counter()
    rows: list[dict] = []

    for case in cases:
        predicted = triage.run(case.item).urgency_tier
        matrix[(case.expected, predicted)] += 1
        rows.append(
            {
                "id": case.id,
                "expected": case.expected,
                "predicted": predicted,
                "correct": case.expected == predicted,
            }
        )
    return dict(matrix), rows


def eval_metrics(matrix: dict[tuple[str, str], int], total: int) -> dict:
    correct = sum(count for (exp, pred), count in matrix.items() if exp == pred)
    accuracy = correct / total if total else 0.0

    red_total = sum(c for (exp, _), c in matrix.items() if exp == "RED")
    green_total = sum(c for (exp, _), c in matrix.items() if exp == "GREEN")
    non_red_total = sum(c for (exp, _), c in matrix.items() if exp != "RED")

    false_red = sum(c for (exp, pred), c in matrix.items() if exp != "RED" and pred == "RED")
    false_green = sum(c for (exp, pred), c in matrix.items() if exp == "RED" and pred == "GREEN")

    return {
        "accuracy": accuracy,
        "false_red_rate": false_red / non_red_total if non_red_total else 0.0,
        "false_green_rate": false_green / red_total if red_total else 0.0,
        "correct": correct,
        "total": total,
    }


def format_confusion_matrix(matrix: dict[tuple[str, str], int]) -> str:
    header = "expected \\ predicted | RED | YELLOW | GREEN"
    lines = [header, "-" * len(header)]
    for expected in TIERS:
        cells = [str(matrix.get((expected, pred), 0)) for pred in TIERS]
        lines.append(f"{expected:16} | " + " | ".join(f"{c:>5}" for c in cells))
    return "\n".join(lines)


@pytest.fixture
def labeled_cases() -> list[LabeledCase]:
    cases = load_labeled_cases()
    assert len(cases) >= 20
    return cases


def test_fixture_count_at_least_twenty(labeled_cases: list[LabeledCase]) -> None:
    assert len(labeled_cases) >= 20


def test_hard_case_water_stain_is_red() -> None:
    cases = load_labeled_cases()
    hard = next(c for c in cases if c.id == "email-001")
    classified = TriageAgent().run(hard.item)
    assert classified.urgency_tier == "RED"
    assert "Reasoning:" in classified.summary


def test_lightbulb_is_green() -> None:
    cases = load_labeled_cases()
    item = next(c for c in cases if c.id == "email-002")
    classified = TriageAgent().run(item.item)
    assert classified.urgency_tier == "GREEN"


def test_eval_accuracy_meets_target(labeled_cases: list[LabeledCase]) -> None:
    matrix, _ = confusion_matrix(labeled_cases)
    metrics = eval_metrics(matrix, len(labeled_cases))

    print("\nBackend:", TriageAgent.backend_name())
    print(format_confusion_matrix(matrix))
    print(
        f"accuracy={metrics['accuracy']:.1%} "
        f"false_red={metrics['false_red_rate']:.1%} "
        f"false_green={metrics['false_green_rate']:.1%}"
    )

    assert metrics["accuracy"] >= 0.9
    assert metrics["false_red_rate"] < 0.15
    assert metrics["false_green_rate"] < 0.02


@pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY") or os.getenv("TRIAGE_USE_STUB", "").lower() in {"1", "true"},
    reason="Set GEMINI_API_KEY (and unset TRIAGE_USE_STUB) for live Gemini eval",
)
def test_gemini_live_eval_accuracy(labeled_cases: list[LabeledCase]) -> None:
    matrix, _ = confusion_matrix(labeled_cases)
    metrics = eval_metrics(matrix, len(labeled_cases))
    assert metrics["accuracy"] >= 0.9
    assert metrics["false_red_rate"] < 0.15
    assert metrics["false_green_rate"] < 0.02
