"""SupervisorNode — plain Python routing (no LLM), per-item failure isolation."""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from agents.ingestion.agent import IngestionAgent
from agents.response.agent import ResponseAgent
from agents.triage.agent import TriageAgent
from db.engine import SessionLocal
from models.core import ClassifiedItem, Draft, RawItem
from session.store import RunStateStore

logger = logging.getLogger(__name__)

CONCURRENCY = 5
MAX_RETRIES = 1  # one bounded retry on transient errors (TDD §2.2)


class SupervisorNode:
    name = "SupervisorNode"

    def __init__(self, run_state: RunStateStore | None = None) -> None:
        self._ingestion = IngestionAgent()
        self._triage = TriageAgent()
        self._response = ResponseAgent()
        self._run_state = run_state or RunStateStore.start_run()

    @property
    def run_state(self) -> RunStateStore:
        return self._run_state

    def ingest_all(self) -> list[RawItem]:
        return self._ingestion.run()

    def process_item(self, raw: RawItem) -> tuple[ClassifiedItem | None, Draft | None, str | None]:
        last_error: str | None = None
        for attempt in range(MAX_RETRIES + 1):
            session = SessionLocal()
            try:
                classified = self._triage.run(raw)
                draft = self._response.run(classified, session)
                self._run_state.record_success(session=session)
                return classified, draft, None
            except Exception as exc:  # noqa: BLE001 — must not halt batch
                session.rollback()
                last_error = str(exc)
                if attempt < MAX_RETRIES:
                    logger.warning(
                        "Item %s attempt %d failed, retrying: %s",
                        raw.id,
                        attempt + 1,
                        exc,
                    )
                    time.sleep(0.05)
                    continue
                logger.exception("Item %s failed after retries: %s", raw.id, exc)
                self._run_state.record_failure(raw.id, last_error, session=session)
                return None, None, "triage_failed"
            finally:
                session.close()
        return None, None, "triage_failed"

    def run_batch(self, raw_items: list[RawItem]) -> list[dict]:
        results: list[dict] = []
        with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
            futures = {pool.submit(self.process_item, raw): raw for raw in raw_items}
            for future in as_completed(futures):
                raw = futures[future]
                classified, draft, err = future.result()
                results.append(
                    {
                        "raw_item_id": raw.id,
                        "classified": classified,
                        "draft": draft,
                        "error": err,
                    }
                )
        self._run_state.finish()
        return results
