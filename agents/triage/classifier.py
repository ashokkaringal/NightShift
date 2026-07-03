"""Urgency classification — Gemini Flash with deterministic rules fallback."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Literal

from pydantic import BaseModel, ValidationError

from agents.triage.prompts import CLASSIFICATION_SYSTEM

logger = logging.getLogger(__name__)

UrgencyTier = Literal["RED", "YELLOW", "GREEN"]
DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_TRIAGE_MODEL", "gemini-2.0-flash")


class ClassificationResult(BaseModel):
    urgency_tier: UrgencyTier
    rationale: str
    summary: str


def use_gemini_classifier() -> bool:
    if os.getenv("TRIAGE_USE_STUB", "").lower() in {"1", "true", "yes"}:
        return False
    return bool(os.getenv("GEMINI_API_KEY"))


def classify_with_rules(raw_text: str) -> ClassificationResult:
    """Deterministic fallback — keeps CI green without an API key."""
    text = raw_text.lower()

    red_patterns = (
        "water stain",
        "no heat",
        "code violation",
        "gas",
        "active leak",
        "actively leaking",
        "leaking from",
        "flooding",
        "fire",
        "smoke",
        "carbon monoxide",
        "broken pipe",
        "sewage",
        "no hot water",
    )
    yellow_patterns = (
        "invoice",
        "mismatch",
        "inspection",
        "drippy faucet",
        "drip",
        "maintenance request",
        "recieved",
        "received my",
        "deadline",
        "hoa fine",
    )
    green_patterns = (
        "lightbulb",
        "no rush",
        "newsletter",
        "pool hours",
        "package room",
        "not urgent",
        "no action needed",
        "confirm you",
        "low priority",
        "cosmetic",
        "no response needed",
    )

    if any(p in text for p in red_patterns):
        tier: UrgencyTier = "RED"
        rationale = "Matches safety, habitability, or code-violation RED pattern."
    elif any(p in text for p in yellow_patterns):
        tier = "YELLOW"
        rationale = "Matches financial, follow-up, or non-emergency maintenance YELLOW pattern."
    elif any(p in text for p in green_patterns):
        tier = "GREEN"
        rationale = "Routine or informational request with no urgency signal."
    else:
        tier = "GREEN"
        rationale = "No RED/YELLOW signals detected; defaulting to GREEN."

    summary = f"{tier} – {raw_text[:100].strip()}..."
    return ClassificationResult(urgency_tier=tier, rationale=rationale, summary=summary)


def _parse_json_response(text: str) -> ClassificationResult:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    data = json.loads(cleaned)
    return ClassificationResult.model_validate(data)


def classify_with_gemini(raw_text: str, property_id: str) -> ClassificationResult:
    from google import genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")

    client = genai.Client(api_key=api_key)
    user_prompt = (
        f"Property ID: {property_id}\n\n"
        f"Inbound message:\n{raw_text}\n\n"
        "Classify urgency and explain briefly."
    )

    response = client.models.generate_content(
        model=DEFAULT_GEMINI_MODEL,
        contents=user_prompt,
        config={
            "system_instruction": CLASSIFICATION_SYSTEM,
            "response_mime_type": "application/json",
        },
    )

    result_text = response.text or ""
    try:
        return _parse_json_response(result_text)
    except (json.JSONDecodeError, ValidationError) as exc:
        logger.warning("Gemini JSON parse failed (%s), falling back to rules", exc)
        return classify_with_rules(raw_text)


def classify_urgency(raw_text: str, property_id: str) -> ClassificationResult:
    if use_gemini_classifier():
        try:
            return classify_with_gemini(raw_text, property_id)
        except Exception as exc:  # noqa: BLE001 — bounded fallback
            logger.warning("Gemini classification failed (%s), using rules fallback", exc)
    return classify_with_rules(raw_text)
