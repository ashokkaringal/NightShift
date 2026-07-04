"""Structured logging configuration."""

from __future__ import annotations

import logging

from observability.redaction import redact_text


class RedactingFormatter(logging.Formatter):
    """Apply PII/secret redaction to log messages (Member D — D2)."""

    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        return redact_text(original)


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(
        RedactingFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
