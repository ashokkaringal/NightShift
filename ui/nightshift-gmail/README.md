# NightShift Gmail-style UI

React + Vite front end for the NightShift HITL demo. Reads staged drafts from the FastAPI UI API and wires manager actions to `hitl/actions.py`.

## Run locally

```bash
# Terminal 1 — API (from repo root)
bash scripts/run_ui_api.sh          # http://localhost:8001

# Terminal 2 — UI
cd ui/nightshift-gmail
npm install
npm run dev                         # http://localhost:5173
```

Requires a populated SQLite DB (`bash scripts/rebuild_dev_db.sh` from repo root).

## Features

| Feature | Description |
|---------|-------------|
| **Sidebar filters** | Inbox, Staged, Urgent (RED), Follow-up (YELLOW), Spam, Approved, Snoozed, Rejected |
| **Dual draft picker** | RED/YELLOW items show Option A (action-focused) and Option B (empathetic) stacked; Approve saves the selected text |
| **Spam folder** | SPAM-classified items; dark blue when unread (`spam_unread` from API); marks read on message click |
| **PDF attachments** | Message body + extracted attachment text + Download link |
| **HITL actions** | Approve, Reject, Snooze, Save edits — same FSM as CLI |

## API proxy

Vite proxies `/api/*` → `http://127.0.0.1:8001` (override with `VITE_API_PROXY`).

## E2E tests

Playwright regression uses dedicated ports `:5174` / `:8002` and `ui_e2e.db` — see `bash scripts/run_ui_e2e.sh` from repo root.
