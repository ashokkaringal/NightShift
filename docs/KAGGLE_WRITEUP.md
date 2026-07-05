# NightShift: Overnight Property Triage with Database-Enforced Human Approval

**Track:** Agents for Business  
**Public repo:** https://github.com/ashokkaringal/NightShift  
**License:** CC-BY-4.0

---

## Hook: NightShift drafts. It never sends.

Property managers for small and mid-size portfolios often wake up to overnight noise: tenant emails, HOA notices, vendor invoices, and city compliance letters scattered across disconnected systems. Triage is slow, context is missing, and the stakes are high. A habitability issue filed as “low priority” can become a code violation; an auto-sent reply can create liability.

Most “approval agent” demos treat human oversight as a UI checkbox. NightShift treats it as **architecture**:

> **NightShift drafts. It never sends. Not because the prompt says so — because phase 1 has no outbound send path, and the database enforces human approval.**

Phase 1 has no Gmail or SMTP integration — nothing in the codebase sends mail. Every outbound draft is written to SQLite with `status=staged`. A manager must explicitly Approve, Reject, or Snooze. The database rejects illegal status transitions (for example, `staged → ready_to_send` without approval) via a finite-state validator and a `CHECK` constraint on allowed status values. Even if an LLM is manipulated by prompt injection, the worst case is a bad *draft* — not a sent email.

NightShift is built for the Google & Kaggle 5-Day AI Agents Intensive capstone. It demonstrates domain-specific judgment (property-management urgency), a multi-agent ADK graph, long-term memory, MCP tool use, and Effective Trust — with a demo path designed to be visceral in under five minutes.

---

## Problem

Overnight inbox volume is a workflow problem and a safety problem:

- **Mis-prioritization:** A tenant message about a ceiling water stain with no active drip can look “minor” but signals early structural water damage — the kind of issue that becomes a city violation if ignored.
- **Cross-source fragmentation:** Email, HOA portals, and invoices arrive in different shapes; managers re-derive context every morning.
- **Outbound risk:** Agents that “helpfully” send replies bypass the manager’s judgment and create legal exposure.

NightShift automates ingestion, classification, and drafting **end-to-end**, while guaranteeing **zero automated outbound action** without explicit human sign-off.

---

## Solution overview

NightShift runs a **three-agent Google ADK 2.0 graph** overnight:

1. **IngestionAgent** — pulls items from read-only MCP tools (`read_inbox`, HOA portal, invoices).
2. **TriageAgent** — classifies urgency as **RED / YELLOW / GREEN / SPAM** using Gemini Flash (with deterministic rules fallback) plus sandbox tools.
3. **ResponseAgent** — drafts replies with Gemini Flash (or rules templates) and persists **two variants** for RED/YELLOW (`draft_text` action-focused + `draft_text_alt` empathetic rules template) as `Draft(status=staged)` in SQLite.

A **SupervisorNode** (plain Python, no LLM) routes each item, isolates failures per item, and records batch progress in `overnight_runs`. One failed classification does not halt the batch.

**Deterministic memory:** `TriageAgent` resolves `tenant_id → property_id` via JSON lookup (`memory/data/tenant_property_map.json`), not LLM guessing. Property personality notes (`property_personality.json`) warm drafts without forwarding full raw email history on every call.

**Human-in-the-loop UI:** A Gmail-style React front end reads staged drafts from the API and calls the same `hitl/actions.py` module as the CLI (`approve`, `reject`, `snooze`, `edit-approve`). RED/YELLOW items show **two stacked draft options** (action-focused vs empathetic); Maria selects one before approve. **Spam** items (`email-010`) route to a dedicated folder with server-side unread tracking (`read_at`). Approve transitions require `approved_by` and `approved_at` — enforced at the database layer, not only in UI code.

**Phase 1 data:** All inbound content comes from curated MCP fixtures (JSON + machine-readable PDF attachments). Phase 2 can swap `read_inbox` for Gmail read-only behind the same `RawItem` contract without changing triage, drafting, or HITL.

---

## Architecture

![NightShift architecture](../docs/architecture.png)

*Embed the diagram above in the Kaggle writeup editor. Source: `docs/architecture.svg`.*

**Important — how the pipeline actually runs:** `python main.py run-overnight` uses **`SupervisorNode`** (`agents/supervisor.py`), not a direct agent-to-agent chain. The supervisor:

1. Calls **`IngestionAgent.run()`** once → **`IngestionAgent` calls MCP read tools** (`read_inbox`, `read_hoa_portal`, `read_invoices_folder`) and returns `list[RawItem]`.
2. For **each** `RawItem`, calls **`TriageAgent.run(raw)`** then **`ResponseAgent.run(classified)`** → staged draft in SQLite.

Agents are **peers invoked by the supervisor**; Ingestion does not pass objects to Triage, and Triage does not pass objects to Response. The **ADK `SequentialAgent`** in `agents/adk/graph.py` declares three named sub-agents for capstone dry-run (`python main.py --dry-run`) — it is topology for judges, not the runtime data pipe.

| Layer | Role |
|-------|------|
| **MCP mock server** | Read-only tools; **called by IngestionAgent** (HTTP or direct loaders). Returns `RawItem`. |
| **SupervisorNode** | Orchestrates batch: ingest_all → per-item triage + response; failure isolation; `overnight_runs` progress. |
| **IngestionAgent** | MCP client — produces `list[RawItem]`; does not classify or draft. |
| **TriageAgent** | One item in → `ClassifiedItem` out; reads memory for property lookup. |
| **ResponseAgent** | One classified item in → `Draft(status=staged)` + optional `draft_text_alt` in SQLite; reads memory for personality notes. At most one Gemini call per item (primary only). |
| **Memory store** | JSON-backed tenant→property map + personality notes (key/value lookup; read by Triage + Response; consolidated offline). |
| **Sandbox tools** | Invoice audit; lease cross-reference (called from TriageAgent). |
| **Security** | Red-team inbound scan; Blue/Green cross-tenant draft validation. |
| **SQLite HITL DB** | Draft FSM; status `sent` is not in the schema. |
| **Manager UI + API** | FastAPI + React; Playwright E2E (8 tests). |

**MCP confused-deputy mitigation:** Tools are read-only in phase 1 — no send/write tools exposed to agents.

**Spec-driven development:** Gherkin features in `features/*.feature` are executable via pytest-bdd. `policy/check_no_send.py` is a release gate.

Optional Docker image exposes `/health` for deploy evidence (`docker/Dockerfile`).

---

## Demo fixtures (four curated beats)

NightShift ships four inbox fixtures tuned for the capstone demo and live-Gemini subset (`GEMINI_LIVE_ONLY_IDS=email-001,email-006,email-007,email-009`). Together they cover **hard triage judgment**, **YELLOW-tier HITL**, and **two PDF deadline patterns**.

### `email-001` — ambiguous water stain → RED

Fixture text: *"The ceiling above my bathroom has a small water stain, has had it for a week, nothing dripping yet."*

This is deliberately borderline — plausibly GREEN (no active leak) or RED (early structural water damage). NightShift classifies **RED** with stated rationale. The morning brief surfaces RED items first; the draft remains **staged** until the manager approves.

This beat demonstrates **judgment**, not just keyword matching — the core of “why agents, specifically” for property management. Tenant `tenant-123` maps via memory to **Oak Street Duplex** (`property-A`).

### `email-006` — follow-up acknowledgment → YELLOW (HITL without RED urgency)

Fixture text: *"Can you confirm you recieved my maintanance request from last week about the drippy faucet?"*

Classified **YELLOW** — a tenant follow-up on an existing maintenance thread, not an immediate habitability emergency. The typo *recieved* is intentional fixture noise; rules and Gemini both land on acknowledgment-tier handling.

**Why it matters for the demo:** Not every overnight item is RED. The UI shows **STAGED** with Approve / Reject / Snooze on a YELLOW draft (yellow_ack template), proving HITL applies across tiers — not only crisis mail. Tenant `tenant-456` → **Valencia Condo** (`property-B`) via memory lookup. GREEN items, by contrast, show **NO REPLY** with no approve button (PRD non-goal: no auto-send even for low priority).

### `email-007` — body says “Friday”; PDF has the real date → RED

Email body: *"City code violation notice scanned copy attached — says exterior stairs need railing repair by Friday."*

PDF attachment (`code-violation-notice.pdf`) contains:

```
CITY CODE VIOLATION NOTICE
Compliance deadline: Friday June 27 2026
```

The body only names a weekday (**Friday**); the authoritative deadline is in the PDF. `extract_deadline()` scores the full PDF phrase **Friday June 27 2026** above the vague weekday hint — the inverse problem to `email-009`. Triage lands **RED** (code violation); draft uses the **red_city_v1** template with the PDF-derived date. Same tenant/property as `email-001` (`tenant-123` / Oak Street Duplex).

### `email-009` — deadline only in PDF → RED

Email body: *"Please review the attached stop-work order from the city inspector."* — **no deadline in the body.**

PDF attachment (`stop-work-order.pdf`) contains:

```
STOP-WORK ORDER
Compliance deadline: Wednesday July 9 2026
```

Pipeline behavior:

1. `mcp/loaders.py` extracts PDF text and merges it into `raw_text` for agents.
2. `extract_deadline()` picks **Wednesday July 9 2026** from the attachment block — there is no competing date in the body.
3. UI shows **split view**: short body, Attachments section with extracted text, and a **Download** button for the source PDF (`GET /attachments/email-009/stop-work-order.pdf`).
4. Draft cites **Wednesday July 9 2026** — derived from the attachment, not the email body.

**Pairing `email-007` and `email-009`:** one fixture hides the date in the PDF while the body mentions a weekday; the other hides the date entirely in the body. Both show why PDF ingestion is load-bearing for property-management compliance mail.

### `email-010` — spam / phishing → SPAM

Fixture text: gift-card prize scam with unsubscribe footer. Classified **SPAM** — no tenant reply drafted, no HITL approve. UI routes to **Spam** folder; unread count uses `read_at` in SQLite (resets on DB rebuild).

---

## Evaluation results

Run: `python main.py eval-urgency` (25 labeled fixtures, rules-stub backend for reproducibility without API keys).

```
expected \ predicted |   RED | YELLOW | GREEN
------------------------------------------------
RED                |    10 |      0 |       0
YELLOW             |     1 |      5 |       0
GREEN              |     0 |      0 |       9

accuracy=96.0%
false_red_rate=6.7%
false_green_rate=0.0%
```

| Metric | Result | PRD target |
|--------|--------|------------|
| Accuracy | 96.0% | ≥ 90% |
| False-RED | 6.7% | < 15% |
| False-GREEN | 0.0% | < 2% |

**Interpretation:** Zero false-GREEN is the safety-critical win — no habitability issue was under-prioritized. One YELLOW item was over-escalated to RED (conservative bias acceptable for demo; live Gemini on subset IDs can refine edge cases). Hard case `email-001` consistently classifies RED.

*Attach a screenshot of the confusion matrix in the Kaggle submission.*

Automated regression: `pytest` (108 passed), `bash scripts/pre_submit.sh`, Playwright E2E (8/8).

---

## Effective Trust (security triad)

NightShift implements **Red / Blue / Green** layers:

**Red team (`security/red_team.py`):** Scans inbound text for prompt-injection patterns before triage prompts run. Blocks obvious “ignore previous instructions” style attacks in fixtures.

**Blue/Green validation (`security/output_validation.py`):** Checks draft output for cross-tenant leakage — another tenant’s email or property name appearing in a draft for the wrong property. Uses the same memory map that powers triage.

**Structural backstop (`db/fsm.py`, `db/models.py`, `policy/check_no_send.py`):** SQLAlchemy `before_update` hook validates FSM transitions. `approved` requires non-null `approved_by` and `approved_at`. Direct insert of `status="sent"` fails the SQLite `CHECK` constraint. Unit tests in `tests/test_state_machine.py` prove these blocks.

**Threat model (phase 1):** Compromised MCP can corrupt *input*, not send mail. Manipulated drafts still require manager approval. Stolen manager credentials are out of scope.

**PII hygiene:** OpenTelemetry spans and logs pass through redaction (`observability/redaction.py`).

---

## Observability

Per-item OpenTelemetry spans cover ingest → triage → draft (`observability/tracing.py`):

- Attributes: `item.id`, `triage_tier`, `property_id`, `draft_status`, agent backend name
- Tool sub-spans: invoice audit, lease cross-ref
- Token usage fields when Gemini is live (`gen_ai.usage.*`)

Default local mode uses in-memory export (`OTEL_USE_MEMORY=1`) — no collector required for demo. Optional OTLP export to a local collector for deeper traces.

Overnight batch metadata (`overnight_runs`: processed count, failed count, timestamps) supports reconstructing a run after restart.

---

## Key course concepts (5 of 6)

| Concept | NightShift implementation |
|---------|---------------------------|
| **Multi-agent systems** | ADK `SequentialAgent` + SupervisorNode with three named sub-agents |
| **Agent tools / MCP** | Read-only MCP mock server; sandbox triage tools |
| **Long-term memory** | JSON tenant→property map + personality notes; consolidation CLI |
| **Effective Trust** | Red/Blue/Green + HITL FSM at database layer |
| **Observability** | OpenTelemetry per-item traces with PII redaction |
| *Agent quality evals* | Partial — rules eval harness + confusion matrix; live Gemini eval optional |

---

## Limitations and phase 2

- **Rules stub vs live Gemini:** CI and keyless clones use deterministic classifiers; live Gemini runs on configurable ID subset (`GEMINI_LIVE_ONLY_IDS`).
- **PDF scope:** Machine-readable PDF text extraction only — no OCR for scanned documents in phase 1.
- **Memory:** JSON key/value files under `memory/data/`; production would use a shared store with nightly consolidation only (no vector DB in phase 1).
- **SQLite:** Single-writer; production would use Postgres with the same FSM logic.
- **No outbound send in phase 1:** Approve records intent only. Phase 2 adds Gmail read-only ingestion; send would remain a separate, gated path calling `policy/check_no_send.py`.

---

## How to reproduce

```bash
git clone https://github.com/ashokkaringal/NightShift.git
cd NightShift
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # optional: GEMINI_API_KEY for live subset

python scripts/generate_pdf_fixtures.py
bash scripts/rebuild_dev_db.sh

python main.py morning-brief   # ranked brief from SQLite
python main.py eval-urgency    # confusion matrix

# UI demo (two extra terminals)
bash scripts/run_ui_api.sh                    # :8001
cd ui/nightshift-gmail && npm install && npm run dev   # :5173

pytest -q && bash scripts/pre_submit.sh
bash scripts/run_ui_e2e.sh
```

**Video demo path:** Safety banner → `email-001` RED triage → `email-006` YELLOW dual-draft HITL → `email-007` PDF date beats “Friday” → `email-009` deadline-only PDF → `email-010` Spam folder → manager Approve (chosen draft option) → headline hook.

---

## Team and acknowledgments

Built for the Google & Kaggle 5-Day AI Agents Intensive (Vibe Coding), Agents for Business track. Spec-driven development guided by PRD/TDD/Gherkin features. Gemini 2.5 Flash (triage) and Gemini 2.5 Flash / Pro (drafting) via Google AI Studio when live mode is enabled.

---

*Word count: ~1,950 (within 2,500 limit). Paste into Kaggle Writeup field; embed `docs/architecture.png` and confusion matrix screenshot; link YouTube video and public repo before submitting.*
