---
name: classification-skill
description: Classify overnight property items as RED, YELLOW, or GREEN urgency
---

# Classification Skill

## Overview

Consumes `RawItem`, performs deterministic property lookup, calls Gemini Flash for tier (Day 2+).

## Workflow

1. Resolve `tenant_id` → `property_id` via memory store
2. Classify urgency tier
3. Emit `ClassifiedItem` — **do not** forward `raw_text`
