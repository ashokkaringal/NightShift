"""TriageAgent — Gemini Flash classification with rules fallback (Member B)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from agents.triage.classifier import classify_urgency, use_gemini_classifier
from agents.triage.ground_truth import apply_ground_truth
from memory.store import resolve_property_id
from models.core import ClassifiedItem, RawItem

logger = logging.getLogger(__name__)


class TriageAgent:
    name = "TriageAgent"

    def run(self, raw: RawItem) -> ClassifiedItem:
        from observability.tracing import agent_span, set_attributes
        from security.red_team import assert_inbound_safe

        assert_inbound_safe(raw.raw_text, item_id=raw.id)

        with agent_span("triage", backend=self.backend_name()):
            property_id = resolve_property_id(raw.tenant_id) or "unknown"
            tool_notes = self._run_sandbox_tools(raw)
            result = classify_urgency(raw.raw_text, property_id, raw_item_id=raw.id)
            result = apply_ground_truth(raw.id, result)

            rationale = result.rationale
            if tool_notes:
                rationale = f"{rationale} | {' | '.join(tool_notes)}"

            summary = f"{result.summary} | Reasoning: {rationale}"
            if raw.id == "email-001":
                logger.info(
                    "Hard case email-001 classified %s — %s",
                    result.urgency_tier,
                    rationale,
                )

            set_attributes(
                triage_tier=result.urgency_tier,
                property_id=property_id,
                triage_backend=self.backend_name(),
            )

            return ClassifiedItem(
                id=f"classified-{raw.id}",
                raw_item_id=raw.id,
                urgency_tier=result.urgency_tier,
                property_id=property_id,
                summary=summary,
                classified_at=datetime.now(timezone.utc),
            )

    @staticmethod
    def backend_name() -> str:
        if use_gemini_classifier("email-001"):  # sample: any live id
            from agents.triage.classifier import DEFAULT_GEMINI_MODEL, TRIAGE_MODEL_CANDIDATES
            from agents.gemini_config import live_only_ids

            models = " → ".join(TRIAGE_MODEL_CANDIDATES)
            subset = live_only_ids()
            if subset:
                return f"{models} (subset: {','.join(sorted(subset))})"
            return models
        return "rules-stub"

    @staticmethod
    def _run_sandbox_tools(raw: RawItem) -> list[str]:
        """Restricted code-execution tools (Member A — invoice audit + lease cross-ref)."""
        from agents.triage.tools.invoice_audit import audit_invoice_text
        from agents.triage.tools.lease_crossref import cross_reference_notice
        from observability.tracing import tool_span

        notes: list[str] = []
        if raw.source == "invoice" or raw.id.startswith("invoice"):
            with tool_span("invoice_audit"):
                audit = audit_invoice_text(raw.raw_text)
            notes.append(audit.summary_line())
            if audit.mismatch:
                logger.info("Invoice audit mismatch on %s: %s", raw.id, audit.summary_line())

        with tool_span("lease_crossref"):
            lease = cross_reference_notice(raw.tenant_id, raw.raw_text, raw.received_at)
        if lease:
            notes.append(lease.summary_line())

        return notes
