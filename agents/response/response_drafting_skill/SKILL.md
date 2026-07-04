---
name: response-drafting-skill
description: Draft professional tenant replies from ClassifiedItem; never send outbound messages
---

# Response Drafting Skill

## Overview

Consumes `ClassifiedItem` only (no `raw_text`). Uses property personality notes from memory.

## Workflow

1. Load property context from memory (display name + personality note)
2. Call Gemini Pro to draft (structured handoff only — no full raw_text)
3. Fall back to rules templates if API fails or `DRAFT_USE_STUB=1`
4. Write `Draft(status=staged)` to database — never auto-send

## Token-saving dev mode

Set `GEMINI_LIVE_ONLY_IDS=email-001,email-006` to run Flash triage + draft on hard case + faucet follow-up.
