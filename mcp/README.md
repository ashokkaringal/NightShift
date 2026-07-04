# NightShift MCP mock server

Read-only mock endpoints for the Google 5-Day Agents course capstone. `IngestionAgent` calls these tools (directly via `mcp/loaders.py` in phase 1, or over HTTP when `MCP_BASE_URL` is set).

## Endpoints

| Method | Path | Auth | Returns |
|--------|------|------|---------|
| GET | `/health` | none | `{"status":"ok"}` |
| GET | `/read_inbox` | Bearer | `list[RawItem]` from `fixtures/inbox.json` |
| GET | `/read_hoa_portal` | Bearer | `list[RawItem]` from `fixtures/hoa_portal.json` |
| GET | `/read_invoices_folder` | Bearer | `list[RawItem]` from `fixtures/invoices/*.txt` and `*.pdf` |

All read tools require:

```http
Authorization: Bearer dev-token-placeholder
```

Configure via `.env`:

```bash
MCP_SERVICE_TOKEN=dev-token-placeholder
MCP_BASE_URL=http://localhost:8000
```

## Run locally

```bash
source .venv/bin/activate
uvicorn mcp.server:app --reload --port 8000
curl http://localhost:8000/health
curl -H "Authorization: Bearer dev-token-placeholder" http://localhost:8000/read_inbox
```

## Fixtures

| Path | Contents |
|------|----------|
| `fixtures/inbox.json` | 8 tenant emails including hard case `email-001` (water stain); `email-007` has a PDF attachment |
| `fixtures/hoa_portal.json` | 3 HOA portal notices (messy typos, inspection dates) |
| `fixtures/invoices/*.txt` | Vendor invoices — `invoice_001` has intentional total mismatch |
| `fixtures/invoices/*.pdf` | Machine-readable invoice PDFs (text extracted via `mcp/pdf_parser.py`) |
| `fixtures/attachments/*.pdf` | Email attachment PDFs merged into inbox `raw_text` at ingest |

### PDF ingestion (phase 1)

- **Supported:** machine-readable PDFs (text layer) via `pypdf`.
- **Not supported:** scanned/image-only PDFs (no OCR in phase 1).
- Email fixtures may list `attachments` in `inbox.json`; extracted text is appended to `raw_text` before triage/drafting.
- Regenerate demo PDF fixtures: `python scripts/generate_pdf_fixtures.py`

Fixtures are **mock data only** in phase 1 — no live Gmail, HOA portal, or vendor APIs.

**Phase 2 (planned):** swap `read_inbox` to Gmail API (`gmail.readonly` only) while keeping the same `RawItem` contract. See README § Phase 2 roadmap.

## Swap-in story

Changing the backing store (real Gmail API, production HOA REST, S3 invoice folder) only requires edits to `mcp/loaders.py` and `mcp/server.py`. Triage and Response agents consume `RawItem` from `models/core.py` and do not depend on fixture file paths.

## Code-execution tools (Member A)

Sandboxed audit helpers live under `agents/triage/tools/` (restricted functions in phase 1):

- **`audit_invoice_text`** — sums line items vs stated total
- **`cross_reference_notice`** — checks notice date against tenant lease window in `memory/data/tenant_property_map.json`

These are invoked by `TriageAgent` during classification, not by MCP HTTP endpoints.
