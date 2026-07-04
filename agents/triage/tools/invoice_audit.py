"""Invoice line-item audit — restricted sandbox placeholder (TDD §2.8).

Receives structured text input only; no filesystem or network access.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_AMOUNT = re.compile(r"\$([\d,]+(?:\.\d{2})?)")
_STATED_TOTAL = re.compile(
    r"(?:stated\s+)?total\s*:\s*\$([\d,]+(?:\.\d{2})?)",
    re.IGNORECASE,
)
_LINE_ITEM = re.compile(
    r"(?P<label>labor|parts|materials|fee|service|line items?)[^$\n]*\$([\d,]+(?:\.\d{2})?)",
    re.IGNORECASE,
)


def _to_float(value: str) -> float:
    return float(value.replace(",", ""))


@dataclass(frozen=True)
class InvoiceAuditResult:
    line_items: tuple[tuple[str, float], ...]
    computed_total: float
    stated_total: float | None
    mismatch: bool
    delta: float | None

    def summary_line(self) -> str:
        if self.stated_total is None:
            return "Invoice audit: no stated total found"
        if self.mismatch:
            return (
                f"Invoice audit: line items sum ${self.computed_total:.2f} "
                f"≠ stated total ${self.stated_total:.2f} (Δ ${self.delta:.2f})"
            )
        return (
            f"Invoice audit: line items sum ${self.computed_total:.2f} "
            f"matches stated total ${self.stated_total:.2f}"
        )


def audit_invoice_text(text: str) -> InvoiceAuditResult:
    """Sum parsed line-item amounts and compare to the stated invoice total."""
    stated_match = _STATED_TOTAL.search(text)
    stated_total = _to_float(stated_match.group(1)) if stated_match else None

    line_items: list[tuple[str, float]] = []
    for match in _LINE_ITEM.finditer(text):
        label = match.group("label").lower()
        amount = _to_float(match.group(2))
        line_items.append((label, amount))

    if not line_items:
        for match in _AMOUNT.finditer(text):
            amount_str = match.group(1)
            if stated_match and amount_str == stated_match.group(1):
                continue
            line_items.append(("amount", _to_float(amount_str)))

    computed = round(sum(amount for _, amount in line_items), 2)
    delta = round(stated_total - computed, 2) if stated_total is not None else None
    mismatch = stated_total is not None and abs(delta or 0) >= 0.01

    return InvoiceAuditResult(
        line_items=tuple(line_items),
        computed_total=computed,
        stated_total=stated_total,
        mismatch=mismatch,
        delta=delta,
    )
