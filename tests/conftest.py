"""Pytest configuration."""

from __future__ import annotations

import os

import pytest

# Isolated in-memory DB per test session — avoids cross-run UNIQUE collisions.
os.environ.setdefault("DB_URL", "sqlite:///:memory:")

from db.init_db import init_db


@pytest.fixture(scope="session", autouse=True)
def _init_test_db() -> None:
    init_db()
