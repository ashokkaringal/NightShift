# NightShift

**NightShift drafts. It never sends. Not because the prompt says so — because the database won't let it.**

Overnight property-management agent for the Google 5-Day AI Agents Intensive (Vibe Coding) capstone. Ingests mock MCP sources, classifies urgency, drafts replies to a staging DB — human approval required before any send path.

## Problem

Property managers wake up to overnight email, HOA notices, tenant reports, and vendor invoices scattered across disconnected systems. Triage is slow, error-prone, and safety-critical — a mis-prioritized habitability issue or an auto-sent reply can create liability.

## Solution overview

NightShift runs a three-agent ADK graph overnight: **IngestionAgent** pulls mock MCP sources, **TriageAgent** classifies urgency (RED / YELLOW / GREEN) with deterministic memory lookup, and **ResponseAgent** drafts replies to SQLite in `staged` status only. A Gmail-style UI lets the manager Approve / Reject / Snooze — but v1 has **no outbound send path**.

> **Mock data only:** All inbound mail comes from `mcp/fixtures/` (JSON + invoice text files). There is no live Gmail, HOA portal, or vendor API in v1.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add GEMINI_API_KEY when using LLM (Day 2+)

python db/init_db.py
python main.py --dry-run          # verify ADK 2.0 graph
python main.py run-overnight      # full stub pipeline

# MCP mock server (separate terminal)
uvicorn mcp.server:app --reload --port 8000

pytest -q
bash scripts/pre_submit.sh
```

### Agents CLI equivalent

This repo uses `python main.py` as the documented equivalent of `agents-cli run` / `agents-cli test`:

| agents-cli | NightShift equivalent |
|------------|----------------------|
| `agents-cli run .` | `python main.py --dry-run` then `python main.py run-overnight` |
| `adk run . "ingest overnight batch"` | `python main.py run-overnight` |
| `agents-cli test` | `pytest tests/ -q` |

The ADK graph is defined in `agents/adk/graph.py` with three named sub-agents.

## Gmail-style UI (HITL demo)

```bash
# Terminal 1 — rebuild DB
bash scripts/rebuild_dev_db.sh

# Terminal 2 — UI API
bash scripts/run_ui_api.sh          # http://localhost:8001

# Terminal 3 — React UI
cd ui/nightshift-gmail && npm run dev   # http://localhost:5173
```

The UI reads `DraftRow` + `FailedItemRow` from SQLite and wires Approve / Reject / Snooze to the same `hitl/actions.py` as the CLI.

### UI regression tests (Playwright)

```bash
bash scripts/run_ui_e2e.sh
```

E2E uses dedicated ports `:8002` / `:5174` and `ui_e2e.db` — separate from dev.

## Architecture

| Layer | Path | Role |
|-------|------|------|
| ADK graph | `agents/adk/graph.py` | `root_agent` — SequentialAgent with 3 sub-agents |
| Supervisor | `agents/supervisor.py` | Plain Python routing + per-item failure isolation |
| MCP | `mcp/server.py`, `mcp/loaders.py` | Read-only mock inbox / HOA / invoices |
| Sandbox tools | `agents/triage/tools/` | Invoice audit + lease cross-reference |
| Contracts | `models/core.py` | `RawItem`, `ClassifiedItem`, `Draft` |
| HITL | `db/models.py`, `db/fsm.py` | CHECK constraint + FSM on update |
| Policy | `policy/check_no_send.py` | Blocks `staged → ready_to_send` |

See [`mcp/README.md`](mcp/README.md) for MCP endpoint contracts.

![NightShift architecture](docs/architecture.png)

Source SVG: [`docs/architecture.svg`](docs/architecture.svg)

## Observability (OpenTelemetry)

Per-item traces cover ingest → triage → draft (`observability/tracing.py`):

- Span attributes: `item.id`, `triage_tier`, `agent.backend`, tool latency
- Token fields when Gemini is live (`gen_ai.usage.*`)
- PII/secrets redacted in spans and logs (`observability/redaction.py`)

```bash
# Default: in-memory spans (no collector required)
OTEL_USE_MEMORY=1 python main.py run-overnight

# Optional: export to local OTLP collector
OTEL_USE_MEMORY=0 OTEL_EXPORTER_ENDPOINT=http://localhost:4317 python main.py run-overnight
```

## Security (Effective Trust)

| Layer | Module | Role |
|-------|--------|------|
| **Red team** | `security/red_team.py` | Blocks prompt-injection patterns before triage |
| **Blue/Green** | `security/output_validation.py` | Catches cross-tenant emails in drafts |
| **Structural** | `db/fsm.py`, `policy/check_no_send.py` | HITL FSM — no auto-send even if LLM is manipulated |

Threat model summary: compromised MCP can corrupt **input**, not send mail; manipulated drafts still require manager approval; v1 does not solve stolen manager credentials.

## Pre-submit checks

```bash
bash scripts/pre_submit.sh   # policy + key scan + dry-run + pytest
bash scripts/scan_keys.sh    # API key pattern scan on tracked files
python policy/check_no_send.py
```

## Project structure

```
nightshift/
├── main.py                 # Supervisor CLI entrypoint
├── agents/                 # Ingestion, Triage, Response + ADK graph
├── mcp/                    # Mock MCP server + fixtures
├── memory/                 # Tenant→property lookup (JSON-backed)
├── models/core.py          # Shared Pydantic contracts
├── db/                     # SQLite + HITL FSM
├── api/                    # FastAPI UI backend
├── ui/nightshift-gmail/    # React HITL demo UI
├── policy/check_no_send.py # SDD no-send guard
├── observability/          # OpenTelemetry + PII redaction
├── security/               # Red-team scan + output validation
├── docs/architecture.png   # Architecture diagram (README + writeup)
├── docker/Dockerfile       # Container + /health
├── features/*.feature        # Gherkin specs (source of truth)
└── tests/                  # pytest + eval harness
```

## Hard case (eval)

`email-001` / `tenant-123`: *"The ceiling above my bathroom has a small water stain…"* → **RED**

Run the regression harness:

```bash
python main.py eval-urgency
pytest tests/eval_urgency.py tests/test_member_b.py tests/test_gherkin_features.py -q
```

**Sample confusion matrix (rules stub, 25 fixtures):**

```
expected \ predicted |   RED | YELLOW | GREEN
------------------------------------------------
RED                |    10 |      0 |       0
YELLOW             |     1 |      5 |       0
GREEN              |     0 |      0 |       9
```

Typical stub run: **96% accuracy**, false-RED **6.7%**, false-GREEN **0%**.

Targets (PRD §1.3): accuracy ≥90%, false-RED <15%, false-GREEN <2%.

Gherkin specs in `features/` are executable via `pytest-bdd` (`tests/test_gherkin_features.py`).

## Commands

```bash
python main.py --dry-run
python main.py run-overnight
python main.py eval-urgency
python main.py consolidate-memory
python main.py morning-brief
python main.py approve --draft-id X --manager "Jane Doe"
python main.py edit-approve --draft-id X --manager "Jane Doe" --text "Edited reply"
python main.py reject --draft-id X
python main.py snooze --draft-id X
python policy/check_no_send.py
pytest tests/ -q
```

## Docker (optional deploy evidence)

```bash
docker build -f docker/Dockerfile -t nightshift .
docker run --rm -p 8080:8080 nightshift
curl http://localhost:8080/health
```

## Scaling notes (TDD §2.6)

- **Concurrency:** `SupervisorNode` processes items with `ThreadPoolExecutor` (default 5 workers when stubs are on; set `GEMINI_CONCURRENCY=1` for free-tier Gemini).
- **Memory:** v1 uses JSON files under `memory/data/`; production would move to a shared store with nightly consolidation only.
- **MCP swap-in:** Replace `mcp/loaders.py` backends without touching triage/response agents.
- **Deploy:** Optional Cloud Run — build from `docker/Dockerfile`, inject `GEMINI_API_KEY` and `MCP_BASE_URL` as env vars.

## Team docs

- [`NightShift_PRD-V7.3.md`](NightShift_PRD-V7.3.md)
- [`NightShift_TDD-V7.3.md`](NightShift_TDD-V7.3.md)
- [`NightShift_Execution_Plan-V7.4.md`](NightShift_Execution_Plan-V7.4.md)
- [`AGENTS.md`](AGENTS.md)

## License

CC-BY-4.0 — see [`LICENSE`](LICENSE).
