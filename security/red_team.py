"""Red-team inbound content scan — prompt-injection patterns (Member D — D3)."""

from __future__ import annotations

import re
from dataclasses import dataclass

_INJECTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "ignore_previous_instructions",
        re.compile(r"ignore (all )?(previous|prior|above) (instructions|prompts)", re.I),
    ),
    (
        "system_prompt_override",
        re.compile(r"(you are now|act as|pretend to be) (a )?(system|admin|root)", re.I),
    ),
    (
        "tool_injection",
        re.compile(r"<\s*/?\s*(system|tool_call|function_call)\s*>", re.I),
    ),
    (
        "credential_exfiltration",
        re.compile(r"(reveal|print|dump|show).{0,40}(api[_ -]?key|secret|password|token)", re.I),
    ),
    (
        "jailbreak_roleplay",
        re.compile(r"do anything now|developer mode enabled|bypass safety", re.I),
    ),
)


class InboundSecurityError(ValueError):
    """Raised when inbound content matches a blocked injection pattern."""


@dataclass(frozen=True)
class InboundScanResult:
    blocked: bool
    pattern: str | None = None
    detail: str | None = None


def scan_inbound_text(text: str, *, item_id: str | None = None) -> InboundScanResult:
    """
    Scan tenant/HOA/invoice text for prompt-injection vectors.
    Returns blocked=True for high-confidence patterns (Red team).
    """
    for name, pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            detail = f"Inbound security scan blocked {item_id or 'item'}: matched {name}"
            return InboundScanResult(blocked=True, pattern=name, detail=detail)
    return InboundScanResult(blocked=False)


def assert_inbound_safe(text: str, *, item_id: str | None = None) -> None:
    result = scan_inbound_text(text, item_id=item_id)
    if result.blocked:
        raise InboundSecurityError(result.detail or "Inbound content blocked by security scan")
