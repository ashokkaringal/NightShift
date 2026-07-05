# NightShift — Agent Project Rules

NightShift drafts. It never sends — phase 1 has no outbound send path; the database enforces manager approval.

## Constraint harness (course Day 1 factory model)

- **No code path** may set draft `status` to `sent` or skip `approved` before `ready_to_send`.
- **HITL:** every outbound draft starts as `staged`; only manager action transitions to `approved`.
- **MCP tools are read-only** in phase 1 — no send/write tools.
- **Never commit** API keys, bearer tokens, or tenant PII in logs or traces.
- **Red/Blue/Green:** scan inbound content (`security/red_team.py`); validate draft output (`security/output_validation.py`); PII redaction in OTel (`observability/redaction.py`).

## Spec-driven development (course Day 5)

- Source of truth: `features/*.feature` (Gherkin BDD).
- Code is disposable; fix implementation to match specs, not the reverse.
- Run `python policy/check_no_send.py` before release tags.

## Stack

- Python 3.11+
- Google ADK 2.0 multi-agent graph (`agents/adk/graph.py`)
- Gemini 2.5 Flash (triage + drafting when live) via `GEMINI_API_KEY`
- Shared contracts: `models/core.py` only — no duplicate data shapes
- Urgency tiers: `RED`, `YELLOW`, `GREEN`, `SPAM`
- Dual drafts: `draft_text` (primary) + `draft_text_alt` (empathetic rules variant) on RED/YELLOW

## Commands

```bash
python main.py --dry-run
uvicorn mcp.server:app --reload --port 8000
pytest tests/ -v
python policy/check_no_send.py
bash scripts/pre_submit.sh
```
