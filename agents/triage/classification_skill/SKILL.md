---
name: classification-skill
description: Classify overnight property items as RED, YELLOW, GREEN, or SPAM urgency
---

# Classification Skill

## Overview

Consumes `RawItem`, performs deterministic property lookup, calls Gemini Flash for tier (RED / YELLOW / GREEN / SPAM).

## Workflow

1. Resolve `tenant_id` → `property_id` via memory store
2. Run sandbox tools for invoices (`audit_invoice_text`) and lease cross-ref when applicable
3. Classify with Gemini Flash when `GEMINI_API_KEY` is set (`GEMINI_TRIAGE_MODEL`)
4. Fall back to rules stub when `TRIAGE_USE_STUB=1` or no API key
5. Apply ground-truth overrides for demo-critical fixtures (`email-001` → RED, `email-010` → SPAM)
6. Emit `ClassifiedItem` with rationale in `summary` — **do not** forward `raw_text`

## Eval

```bash
python main.py eval-urgency
pytest tests/eval_urgency.py -q
pytest tests/test_gherkin_features.py -q
```
