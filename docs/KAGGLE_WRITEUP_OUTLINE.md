# Kaggle Writeup Outline (≤2,500 words)

Use this scaffold for the shared Google Doc and Kaggle submission. Target **1,800–2,100 words**.

## 1. Hook + problem (~300 words)

- Property managers face scattered overnight communications (email, HOA, invoices).
- Safety risk: mis-prioritized habitability issues and unauthorized outbound replies.
- **Headline:** NightShift drafts. It never sends — because the database won't let it.

## 2. Solution overview (~350 words)

- Three-agent ADK graph: Ingestion → Triage → Response.
- Deterministic memory lookup (`tenant_id → property_id`), not LLM guessing.
- HITL staging DB — every draft starts `staged`; manager Approve / Reject / Snooze.
- Mock MCP fixtures only in v1 (no live Gmail).

## 3. Architecture (~400 words)

- Embed `docs/architecture.png`.
- MCP read-only tools (confused-deputy mitigation).
- SQLite FSM + CHECK constraints.
- Optional Docker health endpoint.

## 4. Hard case + eval results (~400 words)

- `email-001` water stain → RED with stated rationale.
- Confusion matrix from `python main.py eval-urgency` (attach screenshot).
- Metrics: accuracy, false-RED, false-GREEN vs PRD targets.

## 5. Effective Trust / security (~350 words)

- **Red team:** inbound prompt-injection scan (`security/red_team.py`).
- **Blue/Green:** cross-tenant draft validation (`security/output_validation.py`).
- **Structural backstop:** HITL FSM even if injection slips through.
- PII redaction in OpenTelemetry spans and logs.

## 6. Observability (~250 words)

- Per-item OTel spans: model, latency, tool timing.
- Token usage fields when Gemini is live.
- Traceability for demo hard case.

## 7. What we learned / limitations (~250 words)

- Rules stub vs live Gemini tradeoffs.
- SQLite single-writer limit; Postgres path for production.
- Out of scope: compromised manager credentials.

## 8. How to reproduce (~200 words)

```bash
git clone <repo>
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
bash scripts/rebuild_dev_db.sh
bash scripts/run_ui_api.sh   # terminal 2
cd ui/nightshift-gmail && npm run dev
pytest -q && bash scripts/pre_submit.sh
```

## Media checklist

- [ ] Cover image attached in Kaggle Media Gallery
- [ ] YouTube link (public, ≤5 min) with hard-case approve demo
- [ ] GitHub public repo link
- [ ] Writeup **Submitted** (not draft) before deadline
