"""ADK 2.0 multi-agent graph — three distinct sub-agents (capstone Key Concept #1)."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from google.adk.agents import BaseAgent, SequentialAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events.event import Event
from google.genai import types
from typing_extensions import override

from agents.ingestion.agent import IngestionAgent
from agents.response.agent import ResponseAgent
from agents.triage.agent import TriageAgent


class _DelegatedAgent(BaseAgent):
    """ADK wrapper — delegates to plain Python agent modules (Member A wiring)."""

    agent_cls: type = BaseAgent
    role: str = ""

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        impl = self.agent_cls()
        summary = f"{self.name}: {self.role}"
        if isinstance(impl, IngestionAgent):
            items = impl.run()
            summary = f"{summary} — ingested {len(items)} RawItem(s)"
        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            branch=ctx.branch,
            content=types.Content(
                role="model",
                parts=[types.Part.from_text(text=summary)],
            ),
        )


ingestion_agent = _DelegatedAgent(
    name="IngestionAgent",
    description=(
        "read_inbox(since) → list[RawItem]; read_hoa_portal(since) → list[RawItem]; "
        "read_invoices_folder() → list[RawItem]. Bearer auth required. Read-only."
    ),
    agent_cls=IngestionAgent,
    role="MCP ingest → RawItem",
)

triage_agent = _DelegatedAgent(
    name="TriageAgent",
    description="Gemini Flash classification + deterministic property lookup; prunes raw_text",
    agent_cls=TriageAgent,
    role="RawItem → ClassifiedItem (raw_text pruned)",
)

response_agent = _DelegatedAgent(
    name="ResponseAgent",
    description="Gemini Pro drafts replies; writes Draft(status=staged) only — never sends",
    agent_cls=ResponseAgent,
    role="ClassifiedItem → staged Draft",
)

root_agent = SequentialAgent(
    name="NightShiftSupervisor",
    description=(
        "NightShift drafts. It never sends — phase 1 has no outbound send path; the database enforces manager approval. "
        "Supervisor routes Ingestion → Triage → Response."
    ),
    sub_agents=[ingestion_agent, triage_agent, response_agent],
)
