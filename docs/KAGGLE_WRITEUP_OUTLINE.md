# Kaggle Writeup Outline (≤2,500 words)

Use this scaffold for the shared Google Doc and Kaggle submission. Target **1,800–2,100 words**.

## 1. Hook + problem (~300 words)

- Property managers face scattered overnight communications (email, HOA, invoices).
- Safety risk: mis-prioritized habitability issues and unauthorized outbound replies.
- **Headline:** NightShift drafts. It never sends. Not because the prompt says so — because phase 1 has no outbound send path, and the database enforces human approval.

## 2. Solution overview (~350 words)

- **SupervisorNode** orchestrates the overnight batch — not a chain where Ingestion hands off to Triage hands off to Response.
- Step 1: Supervisor calls **IngestionAgent** → MCP read tools → `list[RawItem]`.
- Step 2: For each item, Supervisor calls **TriageAgent** (RED / YELLOW / GREEN / **SPAM**) then **ResponseAgent** → staged draft(s) in SQLite.
- Three named ADK sub-agents (`agents/adk/graph.py`) declare topology for `python main.py --dry-run`; runtime uses `SupervisorNode` (`agents/supervisor.py`).
- Deterministic memory lookup (`tenant_id → property_id`) via JSON key/value store — not LLM guessing, not a vector DB in phase 1.
- **Dual drafts (RED/YELLOW):** Option A action-focused (`draft_text`) + Option B empathetic rules template (`draft_text_alt`); Maria picks one in the UI before approve.
- HITL staging DB — every draft starts `staged`; manager Approve / Reject / Snooze; **SPAM** filtered to its own folder (no approve).
- Mock MCP fixtures only in phase 1 (no live Gmail). **Phase 2:** Gmail read-only swap-in behind `read_inbox` (same `RawItem` contract).

## 3. Architecture (~400 words)

- Embed `docs/architecture.png` (source: `docs/architecture.svg`).
- Walk the diagram left → right:
  - **MCP Mock Server** — read-only tools; confused-deputy mitigation (no send/write tools).
  - **SupervisorNode** — dispatches Ingestion, Triage, Response; writes **run metadata** (`overnight_runs`) to SQLite.
  - **Ingestion Agent** — MCP client; `ingest_all` returns `RawItem[]`.
  - **Triage Agent** — Flash + sandbox tools (invoice audit, lease cross-ref); reads Memory Store.
  - **Response Agent** — Flash (primary draft) + rules fallback; reads Memory; writes **staged** drafts to SQLite.
  - **Gemini API** — Flash for triage and response; rules/templates when stubbed or no API key.
  - **Memory Store** — key/value lookup; agents read mid-run; **violet arrow** = offline write via `memory/consolidate.py` (between batches only).
  - **Security + Observability** — red-team inbound scan, Blue/Green draft validation, OpenTelemetry, SQLite FSM.
  - **SQLite HITL DB** + **Manager UI + API** — Approve / Reject / Snooze; no auto-send path.
- Caption: *Agents never call each other; ADK graph = dry-run topology.*
- Optional Docker `/health` endpoint.

## 4. Hard case + eval results (~400 words)

- `email-001` water stain → RED with stated rationale.
- **`email-006` YELLOW HITL** — dual draft picker (action vs empathetic); approve saves chosen text.
- **`email-009` PDF beat:** body has no deadline; stop-work PDF attachment supplies `Wednesday July 9 2026`; UI shows split body + Attachments + Download; draft cites PDF date.
- **`email-010` SPAM** — gift-card scam; Spam folder with server-side unread (`read_at`).
- Confusion matrix from `python main.py eval-urgency` (attach screenshot).
- Metrics: accuracy, false-RED, false-GREEN vs PRD targets.

## 5. Effective Trust / security (~350 words)

- **Red team:** inbound prompt-injection scan (`security/red_team.py`).
- **Blue/Green:** cross-tenant draft validation (`security/output_validation.py`).
- **Structural backstop:** HITL FSM even if injection slips through.
- PII redaction in OpenTelemetry spans and logs.

## 6. Observability (~250 words)

- Per-item OTel spans: model, latency, tool timing.
- Token usage fields when Gemini is live (at most one Gemini draft call per item — Option B is rules-only).
- Traceability for demo hard case.

## 7. What we learned / limitations (~250 words)

- Rules stub vs live Gemini tradeoffs; `GEMINI_LIVE_ONLY_IDS` for demo subset.
- Dual drafts: primary may use Gemini; alternate is deterministic empathetic template (no second API call).
- Memory: JSON key/value in phase 1; consolidation offline only.
- SQLite single-writer limit; Postgres path for production.
- Out of scope: compromised manager credentials.

## 8. How to reproduce (~200 words)

```bash
git clone https://github.com/ashokkaringal/NightShift.git
cd NightShift
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python scripts/generate_pdf_fixtures.py
bash scripts/rebuild_dev_db.sh
bash scripts/run_ui_api.sh   # terminal 2 — :8001
cd ui/nightshift-gmail && npm install && npm run dev   # :5173
pytest -q && bash scripts/pre_submit.sh
```

## Media checklist

- [ ] Cover image attached in Kaggle Media Gallery
- [ ] Embed `docs/architecture.png` in writeup body
- [ ] YouTube link (public, ≤5 min) — hard case + dual draft + PDF + approve demo
- [ ] GitHub public repo link
- [ ] Confusion matrix screenshot
- [ ] Writeup **Submitted** (not draft) before deadline
