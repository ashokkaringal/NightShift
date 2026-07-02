"""FastAPI MCP mock server (course Day 2)."""

from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI, Header, HTTPException

from mcp.auth import validate_token
from mcp.loaders import read_hoa_portal, read_inbox, read_invoices_folder

app = FastAPI(title="NightShift MCP Mock", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/read_inbox")
def api_read_inbox(
    since: str | None = None,
    authorization: str | None = Header(default=None),
) -> list[dict]:
    validate_token(authorization)
    since_dt = datetime.fromisoformat(since) if since else None
    token = authorization.split(" ", 1)[1] if authorization else None
    try:
        items = read_inbox(since_dt, token=token)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return [i.model_dump(mode="json") for i in items]


@app.get("/read_hoa_portal")
def api_read_hoa_portal(
    since: str | None = None,
    authorization: str | None = Header(default=None),
) -> list[dict]:
    validate_token(authorization)
    since_dt = datetime.fromisoformat(since) if since else None
    token = authorization.split(" ", 1)[1] if authorization else None
    try:
        items = read_hoa_portal(since_dt, token=token)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return [i.model_dump(mode="json") for i in items]


@app.get("/read_invoices_folder")
def api_read_invoices_folder(
    authorization: str | None = Header(default=None),
) -> list[dict]:
    validate_token(authorization)
    token = authorization.split(" ", 1)[1] if authorization else None
    try:
        items = read_invoices_folder(token=token)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return [i.model_dump(mode="json") for i in items]
