---
name: ingestion-skill
description: Read overnight items from MCP mock inbox, HOA portal, and invoices folder
---

# Ingestion Skill

## Overview

Calls read-only MCP tools and returns deduplicated `RawItem` objects.

## Workflow

1. `read_inbox(since)`
2. `read_hoa_portal(since)`
3. `read_invoices_folder()`
4. Dedupe by `id`
