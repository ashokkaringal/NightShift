---
name: response-drafting-skill
description: Draft professional tenant replies from ClassifiedItem; never send outbound messages
---

# Response Drafting Skill

## Overview

Consumes `ClassifiedItem` only (no `raw_text`). Uses property personality notes from memory. Produces **two variants** for RED/YELLOW items.

## Workflow

1. Load property context from memory (display name + personality note)
2. **Option A (primary):** Call Gemini Flash to draft when live (`GEMINI_LIVE_ONLY_IDS`); else rules template (`red_urgent_v1`, etc.)
3. **Option B (alternate):** Always rules empathetic template (`red_urgent_v2_empathetic`, etc.) — no second Gemini call
4. Validate both outputs (`security/output_validation.py`)
5. Write `Draft(status=staged)` with `draft_text` + `draft_text_alt` to database — never auto-send
6. GREEN / SPAM → no tenant reply (single placeholder text, no alternate)

## Token-saving dev mode

Set `GEMINI_LIVE_ONLY_IDS=email-001,email-006,email-007,email-009` to run Flash triage + draft on demo subset only.

## Manager UI

Maria selects Option A or B in the Gmail-style UI; Approve calls `edit-approve` with the chosen text.
