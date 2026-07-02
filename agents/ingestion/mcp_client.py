"""HTTP client for MCP mock server (optional — loaders used for Day 1 local ingest)."""

from __future__ import annotations

import os
from datetime import datetime

import httpx

from mcp.auth import bearer_headers
from models.core import RawItem

MCP_BASE_URL = os.getenv("MCP_BASE_URL", "http://127.0.0.1:8000")


def read_inbox_remote(since: datetime | None = None) -> list[RawItem]:
    params = {}
    if since is not None:
        params["since"] = since.isoformat()
    with httpx.Client(timeout=10.0) as client:
        resp = client.get(
            f"{MCP_BASE_URL}/read_inbox",
            params=params,
            headers=bearer_headers(),
        )
        resp.raise_for_status()
        return [RawItem.model_validate(row) for row in resp.json()]
