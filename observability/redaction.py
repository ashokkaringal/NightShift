"""PII and secret redaction for logs and OpenTelemetry spans (Member D — D2)."""

from __future__ import annotations

import re
from typing import Any

_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE = re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}\b")
_GEMINI_KEY = re.compile(r"AIza[0-9A-Za-z_-]{20,}")
_OPENAI_KEY = re.compile(r"sk-[a-zA-Z0-9]{20,}")
_GITHUB_TOKEN = re.compile(r"ghp_[0-9A-Za-z]{20,}")
_BEARER = re.compile(r"Bearer\s+[A-Za-z0-9._\-]+", re.IGNORECASE)

_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (_GEMINI_KEY, "[REDACTED_GEMINI_KEY]"),
    (_OPENAI_KEY, "[REDACTED_OPENAI_KEY]"),
    (_GITHUB_TOKEN, "[REDACTED_GITHUB_TOKEN]"),
    (_BEARER, "Bearer [REDACTED_TOKEN]"),
    (_EMAIL, "[REDACTED_EMAIL]"),
    (_PHONE, "[REDACTED_PHONE]"),
)

SENSITIVE_ATTRIBUTE_KEYS = frozenset(
    {
        "tenant.email",
        "tenant_id",
        "raw_text",
        "draft_text",
        "gemini.api_key",
        "authorization",
    }
)


def redact_text(value: str) -> str:
    """Redact secrets and tenant PII from free-form text."""
    redacted = value
    for pattern, replacement in _PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return redact_mapping(value)
    if isinstance(value, (list, tuple)):
        return [redact_value(item) for item in value]
    return redact_text(str(value))


def redact_mapping(data: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in data.items():
        if key in SENSITIVE_ATTRIBUTE_KEYS and isinstance(value, str):
            out[key] = redact_text(value)
        else:
            out[key] = redact_value(value)
    return out


def safe_span_attribute(key: str, value: Any) -> tuple[str, Any]:
    """Return a span attribute key/value pair safe for OTel export."""
    if key in SENSITIVE_ATTRIBUTE_KEYS:
        return key, redact_value(value)
    if isinstance(value, str):
        return key, redact_text(value)
    return key, value
