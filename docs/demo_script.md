# NightShift Demo Script (2-minute hard-case segment)

Full UI setup: see [README § Gmail-style UI](../README.md#gmail-style-ui-hitl-demo).

## Setup

```bash
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add GEMINI_API_KEY; tune GEMINI_LIVE_ONLY_IDS (below)

python scripts/generate_pdf_fixtures.py   # once — email-007 / email-009 PDF attachments
bash scripts/rebuild_dev_db.sh            # fresh overnight run → nightshift.db

# Terminal 2: bash scripts/run_ui_api.sh   (:8001)
# Terminal 3: cd ui/nightshift-gmail && npm run dev   (:5173)
```

## Beat 1 — Problem (15 sec)

> "Property managers wake up to dozens of overnight emails. NightShift triages them overnight but **never sends** — every draft stays staged until a human approves."

Point at the safety banner:

> "Phase 1 records manager approval only — there is no outbound send path."

## Gemini live subset (default from `.env.example`)

Default: `TRIAGE_USE_STUB=0`, `DRAFT_USE_STUB=0` — add `GEMINI_API_KEY` and rebuild. Live Gemini runs on demo fixtures only (saves quota):

```bash
TRIAGE_USE_STUB=0
DRAFT_USE_STUB=0
GEMINI_TRIAGE_MODEL=gemini-2.5-flash,gemini-3.5-flash
GEMINI_DRAFT_MODEL=gemini-2.5-flash,gemini-3.5-flash
GEMINI_LIVE_ONLY_IDS=email-001,email-006,email-007,email-009
```

| ID | Tier | Subject | Demo role |
|----|------|---------|-----------|
| `email-001` | **RED** | Bathroom ceiling water stain | Hard case (eval) |
| `email-006` | **YELLOW** | Drippy faucet follow-up | HITL on non-RED tier |
| `email-007` | **RED** | City code violation notice | PDF date beats “Friday” in body |
| `email-009` | **RED** | Stop-work order notice | **Deadline only in PDF** |

After changing `.env`:

```bash
bash scripts/rebuild_dev_db.sh
```

In the UI: open **Inbox** (not only "Urgent RED") to see RED + YELLOW mix.

## Beat 2 — Hard case triage (45 sec)

Show `mcp/fixtures/inbox.json` item `email-001` (water stain, no drip, one week).

```bash
python main.py morning-brief
```

Point out on screen:

- **RED** tier first
- Rationale: *"small water stain... for a week"* → early structural water-damage pattern
- Draft status: **staged** (not sent)

## Beat 2b — PDF attachment (`email-009`) (30 sec)

**Best UI demo for PDF ingestion** — deadline exists only in the attachment.

1. In the UI search box, type `stop-work`
2. Select **Stop-work order notice** (`email-009`, RED, **17:30**)
3. In the detail pane, show **three layers**:
   - **Message body** — one line only: *"Please review the attached stop-work order…"* (no deadline)
   - **Attachments** — `stop-work-order.pdf` with extracted text including **`Compliance deadline: Wednesday July 9 2026`**
   - Click **Download** — real PDF file (read-only fixture; audit trail for manager)
4. Scroll to **NightShift draft reply** — draft should cite **Wednesday July 9 2026** (from PDF via `extract_deadline()`, not from body text)
5. Optional compare **`email-007`**: body says “by Friday”; attachment + draft use full **`June 27 2026`**

Voiceover hook:

> "The email body doesn't contain the deadline — only the PDF does. NightShift extracts attachment text for triage and drafting, while the manager can download the source document."

## Beat 2c — Architecture swap-in (15 sec, optional)

Show [`docs/architecture.png`](../docs/architecture.png):

> "**SupervisorNode** orchestrates the overnight batch — it is not a chain where Ingestion hands off to Triage hands off to Response. Step one: Supervisor calls **IngestionAgent**, which **calls** the read-only MCP tools and returns a list of `RawItem`s. Step two: for each item, Supervisor calls **TriageAgent**, then **ResponseAgent**, which writes a **staged** draft to SQLite. Phase 1 uses fixture MCP; **phase 2** swaps the MCP loader behind `read_inbox` without changing Supervisor or HITL. NightShift still never sends."

## Beat 3 — Manager approve (30 sec)

### CLI

Copy `draft_id` for `email-001` from the brief, then:

```bash
python main.py approve --draft-id <draft-id> --manager "Jane Doe"
python main.py morning-brief
```

Show draft moved to **approved** with manager name + timestamp.

Other HITL actions:

```bash
python main.py edit-approve --draft-id <draft-id> --manager "Jane Doe" --text "Edited reply..."
python main.py reject --draft-id <draft-id>
python main.py snooze --draft-id <draft-id>
```

### UI (Gmail-style demo)

With API on `:8001` and UI on `:5173`:

1. Open **Inbox** → select `email-001` (RED water stain) **or** finish on `email-009` after Beat 2b
2. Confirm badge shows **STAGED** and draft text is visible
3. Click **Approve draft** — badge becomes **APPROVED** (outbound send still disabled in phase 1)
4. Optional: **Reject**, **Snooze**, or edit text + **Save edits** on a YELLOW item (`email-006`)

GREEN items show **NO REPLY** — no Approve button (PRD non-goal: no auto-send even for GREEN).

**Dual draft picker (RED / YELLOW):** Open `email-003` (no heat, RED) or `email-006` (YELLOW). Scroll to **NightShift draft reply** — two stacked options:

1. **Option A — Action-focused** (vendor timeline; may be Gemini on live subset)
2. **Option B — Empathetic** (warmer tone; rules template)

Click Option B → **Approve draft** — chosen text is saved via `edit-approve`. Voiceover:

> "NightShift gives Maria two tone options — she picks one, edits if needed, then approves. Still no send path in phase 1."

**Spam folder:** Sidebar **Spam** shows `email-010` (gift-card scam). Folder is dark blue while unread; click the message to mark read (`POST /drafts/{id}/mark-read`). No HITL approve for SPAM.

**Regression check:** reject on a staged item keeps the detail pane on the same message (Playwright: `bash scripts/run_ui_e2e.sh`).

## Beat 4 — Safety hook (15 sec)

> "NightShift drafts. It never sends. Not because the prompt says so — because phase 1 has no outbound send path, and the database enforces human approval."

Optional: attempt invalid transition in tests:

```bash
pytest tests/test_state_machine.py -v
```

## Beat 5 — Failed items (15 sec)

If any `triage_failed` rows exist, brief shows:

**"COULD NOT CLASSIFY — NEEDS MANUAL REVIEW"**

## Phase 2 teaser (post-capstone, 10 sec)

> "Next we wire `read_inbox` to a test Gmail account with read-only OAuth — same `RawItem` pipeline, still no send scope. Fixtures stay the default for eval and CI."

See README **Phase 2 roadmap — real Gmail**.
