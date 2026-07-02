"""SQLite engine and session factory."""

from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

DB_URL = os.getenv("DB_URL", "sqlite:///nightshift.db")

connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}
_engine_kwargs: dict = {"echo": False, "future": True, "connect_args": connect_args}
if DB_URL in {"sqlite:///:memory:", "sqlite://"}:
    _engine_kwargs["poolclass"] = StaticPool

engine = create_engine(DB_URL, **_engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
