#!/usr/bin/env python3
"""Generate machine-readable PDF fixtures for MCP ingestion tests."""

from __future__ import annotations

import sys
from pathlib import Path

from fpdf import FPDF

ROOT = Path(__file__).resolve().parent.parent


def write_text_pdf(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = FPDF()
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    for line in lines:
        pdf.cell(0, 8, line, new_x="LMARGIN", new_y="NEXT")
    pdf.output(str(path))


def main() -> None:
    fixtures = ROOT / "mcp" / "fixtures"

    write_text_pdf(
        fixtures / "attachments" / "email-007-notice.pdf",
        [
            "CITY CODE VIOLATION NOTICE",
            "Property: Oak Street Duplex",
            "Violation: exterior stairs railing repair required",
            "Compliance deadline: Friday June 27 2026",
            "Failure to repair may result in daily fines.",
        ],
    )

    write_text_pdf(
        fixtures / "attachments" / "email-009-stop-work.pdf",
        [
            "STOP-WORK ORDER",
            "Property: Oak Street Duplex",
            "Violation: exterior work halted pending railing repair",
            "Compliance deadline: Wednesday July 9 2026",
            "Contact: City Building Department",
        ],
    )

    write_text_pdf(
        fixtures / "invoices" / "invoice_elevator.pdf",
        [
            "Invoice #9901 - Metro Elevator Co.",
            "Service: elevator maintenance inspection",
            "Line items: labor $450.00, parts $120.00",
            "Stated total: $570.00",
        ],
    )

    print("PDF fixtures written under mcp/fixtures/")


if __name__ == "__main__":
    main()
