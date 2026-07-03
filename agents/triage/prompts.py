"""Prompt templates for TriageAgent classification."""

CLASSIFICATION_SYSTEM = """You classify overnight property-management inbound items as RED, YELLOW, or GREEN.

RED — safety, habitability, legal/code risk, active damage, gas/leak/fire, no heat in cold weather.
YELLOW — financial mismatch, non-urgent maintenance follow-up, inspection deadlines, ambiguous damage.
GREEN — routine, cosmetic, informational, no time pressure.

Respond with JSON only:
{
  "urgency_tier": "RED" | "YELLOW" | "GREEN",
  "rationale": "1-2 sentences explaining the tier",
  "summary": "One-line manager-facing summary without quoting the full email"
}

Do not include tenant PII beyond what is needed in the summary."""
