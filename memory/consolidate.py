"""Nightly memory consolidation — agents do not write memory mid-run (TDD §2.3)."""

from __future__ import annotations

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
ALLOWED_FILES = ("tenant_property_map.json", "property_personality.json")


def consolidate(source_dir: Path | None = None, *, data_dir: Path | None = None) -> dict[str, int]:
    """
    Merge validated JSON snapshots from source_dir into memory/data/.
    Agents remain read-only during overnight runs; consolidation runs between batches.
    """
    target_root = data_dir or DATA_DIR
    src = source_dir or (target_root / "incoming")
    if not src.exists():
        return {"merged": 0, "skipped": 0}

    merged = 0
    skipped = 0
    for name in ALLOWED_FILES:
        incoming = src / name
        if not incoming.exists():
            continue
        try:
            payload = json.loads(incoming.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            skipped += 1
            continue
        if not isinstance(payload, list):
            skipped += 1
            continue

        target = target_root / name
        existing = []
        if target.exists():
            existing = json.loads(target.read_text(encoding="utf-8"))
        by_key = {
            _row_key(row): row
            for row in existing
            if isinstance(row, dict)
        }
        for row in payload:
            if not isinstance(row, dict):
                skipped += 1
                continue
            by_key[_row_key(row)] = row
            merged += 1

        target.write_text(json.dumps(list(by_key.values()), indent=2) + "\n", encoding="utf-8")

    return {"merged": merged, "skipped": skipped}


def _row_key(row: dict) -> str:
    if "tenant_id" in row:
        return f"tenant:{row['tenant_id']}"
    if "property_id" in row:
        return f"property:{row['property_id']}"
    return json.dumps(row, sort_keys=True)
