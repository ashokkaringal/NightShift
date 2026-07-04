"""Pytest configuration."""

from __future__ import annotations

import os

import pytest

# Isolated in-memory DB per test session — avoids cross-run UNIQUE collisions.
os.environ.setdefault("DB_URL", "sqlite:///:memory:")
os.environ.setdefault("TRIAGE_USE_STUB", "1")
os.environ.setdefault("DRAFT_USE_STUB", "1")
os.environ.setdefault("OTEL_USE_MEMORY", "1")

from db.init_db import init_db
from observability.tracing import setup_tracing


@pytest.fixture(scope="session", autouse=True)
def _init_test_db() -> None:
    setup_tracing(force_memory=True)
    init_db()
