"""IngestionAgent — MCP read tools → RawItem stream."""

from __future__ import annotations

from datetime import datetime

from mcp.loaders import ingest_all_sources


class IngestionAgent:
    name = "IngestionAgent"

    def run(self, since: datetime | None = None) -> list:
        return ingest_all_sources(since)
