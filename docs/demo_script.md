# NightShift Demo Script (2-minute hard-case segment)

## Setup

```bash
source .venv/bin/activate
python db/init_db.py
python main.py run-overnight
```

## Beat 1 — Problem (15 sec)

> "Property managers wake up to dozens of overnight emails. NightShift triages them overnight but **never sends** — every draft stays staged until a human approves."

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

Copy `draft_id` for `email-001` from the brief, then:

```bash
python main.py approve --draft-id <draft-id> --manager "Jane Doe"
python main.py morning-brief
```

Show draft moved to **approved** with manager name + timestamp.

## Beat 4 — Safety hook (15 sec)

> "NightShift drafts. It never sends — because the database won't let it."

Optional: attempt invalid transition in tests:

```bash
pytest tests/test_state_machine.py -v
```

## Beat 5 — Failed items (15 sec)

If any `triage_failed` rows exist, brief shows:

**"COULD NOT CLASSIFY — NEEDS MANUAL REVIEW"**
