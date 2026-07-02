---
name: response-drafting-skill
description: Draft professional tenant replies from ClassifiedItem; never send outbound messages
---

# Response Drafting Skill

## Overview

Consumes `ClassifiedItem` only (no `raw_text`). Uses property personality notes from memory.

## Workflow

1. Load property context from memory
2. Call Gemini Pro to draft (Day 3+)
3. Write `Draft(status=staged)` to database — never auto-send
