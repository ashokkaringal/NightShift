# NightShift Demo Script (2-minute hard-case segment)

## Setup

```bash
source .venv/bin/activate
python db/init_db.py
python main.py run-overnight
```

## Beat 1 — Problem (15 sec)

> "Property managers wake up to dozens of overnight emails. NightShift triages them overnight but **never sends** — every draft stays staged until a human approves."

## Gemini demo pair (RED + YELLOW)

In `.env` set:

```bash
GEMINI_LIVE_ONLY_IDS=email-001,email-006
```

| ID | Tier | Subject |
|----|------|---------|
| `email-001` | **RED** | Bathroom ceiling water stain |
| `email-006` | **YELLOW** | Drippy faucet follow-up |

Avoid `email-007` in this list — it is also **RED** (city code violation).

```bash
rm -f nightshift.db && python db/init_db.py && python main.py run-overnight
```

In the UI: open **Inbox** (not only "Urgent RED") to see both tiers.

## Beat 2 — Hard case triage (45 sec)

Show `mcp/fixtures/inbox.json` item `email-001` (water stain, no drip, one week).

```bash
python main.py morning-brief
```

Point out on screen:

- **RED** tier first
- Rationale: *"small water stain... for a week"* → early structural water-damage pattern
- Draft status: **staged** (not sent)

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

1. Open **Inbox** → select `email-001` (RED water stain)
2. Confirm badge shows **STAGED** and draft text is visible
3. Click **Approve draft** — badge becomes **APPROVED** (still no send path)
4. Optional: **Reject**, **Snooze**, or edit text + **Save edits** on a YELLOW item (`email-006`)

GREEN items show **NO REPLY** — no Approve button (PRD non-goal: no auto-send even for GREEN).

## Beat 4 — Safety hook (15 sec)

> "NightShift drafts. It never sends — because the database won't let it."

Optional: attempt invalid transition in tests:

```bash
pytest tests/test_state_machine.py -v
```

## Beat 5 — Failed items (15 sec)

If any `triage_failed` rows exist, brief shows:

**"COULD NOT CLASSIFY — NEEDS MANUAL REVIEW"**
