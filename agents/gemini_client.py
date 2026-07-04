"""Shared Gemini client — retries, model fallbacks, rate-limit safety."""

from __future__ import annotations

import logging
import os
import re
import time
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_RETRY_ATTEMPTS = int(os.getenv("GEMINI_RETRY_ATTEMPTS", "3"))


def _parse_retry_seconds(exc: Exception) -> float:
    text = str(exc)
    match = re.search(r"retry in ([0-9.]+)s", text, re.IGNORECASE)
    if match:
        return float(match.group(1)) + 0.5
    match = re.search(r"'retryDelay': '([0-9]+)s'", text)
    if match:
        return float(match.group(1)) + 0.5
    return 2.0


def model_candidates(env_var: str, default: str) -> list[str]:
    raw = os.getenv(env_var, default)
    return [part.strip() for part in raw.split(",") if part.strip()]


def generate_content(
    *,
    models: list[str],
    contents: str,
    system_instruction: str | None = None,
    response_mime_type: str | None = None,
    max_output_tokens: int | None = None,
) -> tuple[str, str]:
    """Try models in order; return (text, model_used). Raises last error if all fail."""
    from google import genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")

    client = genai.Client(api_key=api_key)
    last_exc: Exception | None = None

    for model in models:
        for attempt in range(DEFAULT_RETRY_ATTEMPTS):
            try:
                config: dict[str, Any] = {}
                if system_instruction:
                    config["system_instruction"] = system_instruction
                if response_mime_type:
                    config["response_mime_type"] = response_mime_type
                if max_output_tokens is not None:
                    config["max_output_tokens"] = max_output_tokens

                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config or None,
                )
                text = (response.text or "").strip()
                if not text:
                    raise ValueError(f"{model} returned empty text")
                if response.candidates:
                    finish = getattr(response.candidates[0], "finish_reason", None)
                    if str(finish) == "FinishReason.MAX_TOKENS":
                        logger.warning("%s hit MAX_TOKENS — consider raising GEMINI_DRAFT_MAX_TOKENS", model)
                return text, model
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                err = str(exc)
                if "429" in err or "RESOURCE_EXHAUSTED" in err:
                    # Daily quota exhausted (limit: 0) — skip retries and next model immediately.
                    if "limit: 0" in err or "PerDay" in err:
                        logger.warning("%s daily quota exhausted — trying next model", model)
                        break
                    delay = _parse_retry_seconds(exc)
                    logger.warning(
                        "%s rate-limited (attempt %d/%d), retry in %.1fs",
                        model,
                        attempt + 1,
                        DEFAULT_RETRY_ATTEMPTS,
                        delay,
                    )
                    time.sleep(delay)
                    continue
                if "404" in err or "NOT_FOUND" in err:
                    logger.warning("%s not available — trying next model", model)
                    break
                raise
    if last_exc:
        raise last_exc
    raise RuntimeError("No Gemini models configured")
