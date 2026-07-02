# NightShift

**NightShift drafts. It never sends. Not because the prompt says so — because the database won't let it.**

Overnight property-management agent for the Google 5-Day AI Agents Intensive (Vibe Coding) capstone. Ingests mock MCP sources, classifies urgency, drafts replies to a staging DB — human approval required before any send path.

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

## Architecture (Day 1)

| Layer | Path | Role |
|-------|------|------|
| ADK graph | `agents/adk/graph.py` | `root_agent` — SequentialAgent with 3 sub-agents |
| Supervisor | `agents/supervisor.py` | Plain Python routing + per-item failure isolation |
| MCP | `mcp/server.py`, `mcp/loaders.py` | Read-only mock inbox / HOA / invoices |
| Contracts | `models/core.py` | `RawItem`, `ClassifiedItem`, `Draft` |
| HITL | `db/models.py`, `db/fsm.py` | CHECK constraint + FSM on update |
| Policy | `policy/check_no_send.py` | Blocks `staged → ready_to_send` |

## Hard case (eval)

`email-001` / `tenant-123`: *"The ceiling above my bathroom has a small water stain…"* → **RED**

## Commands (full week)

```bash
adk run . "ingest overnight batch"     # ADK 2.0 graph (or: python main.py --dry-run)
python main.py run-overnight           # Supervisor pipeline + persisted run state
python main.py morning-brief        # Day 3
python main.py approve --draft-id X --manager "Jane Doe"
python policy/check_no_send.py      # SDD policy check
pytest -q                           # or: adk eval (when eval sets added)
```

## Team docs

- [`NightShift_PRD-V7.3.md`](NightShift_PRD-V7.3.md)
- [`NightShift_TDD-V7.3.md`](NightShift_TDD-V7.3.md)
- [`NightShift_Execution_Plan-V7.4.md`](NightShift_Execution_Plan-V7.4.md) — current team schedule ([PDF](NightShift_Execution_Plan-V7.4.pdf))
- [`AGENTS.md`](AGENTS.md)

## License

CC-BY-4.0 — see [`LICENSE`](LICENSE).
