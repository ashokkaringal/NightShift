---
name: classification-skill
description: Classify overnight property items as RED, YELLOW, or GREEN urgency
---

# Classification Skill

## Overview

Consumes `RawItem`, performs deterministic property lookup, calls Gemini Flash for tier.

## Workflow

1. Resolve `tenant_id` → `property_id` via memory store
2. Classify with `gemini-2.0-flash` when `GEMINI_API_KEY` is set
3. Fall back to rules stub when `TRIAGE_USE_STUB=1` or no API key
4. Emit `ClassifiedItem` with rationale in `summary` — **do not** forward `raw_text`
