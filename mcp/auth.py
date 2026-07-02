"""Bearer token validation for MCP HTTP server."""

from __future__ import annotations

import os

from fastapi import HTTPException

DEV_TOKEN = os.getenv("MCP_SERVICE_TOKEN", "dev-token-placeholder")


def validate_token(authorization: str | None) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    if token != DEV_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")


def bearer_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {DEV_TOKEN}"}
