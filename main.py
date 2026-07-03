#!/usr/bin/env python3
"""
NightShift supervisor entrypoint.

Data flow (hard case — PRD §1.5 / TDD §2.2.1):
  IngestionAgent → water-stain RawItem via read_inbox (MCP)
  TriageAgent    → ClassifiedItem urgency=RED
  ResponseAgent  → Draft(status=staged) in SQLite
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from agents.adk.graph import root_agent
from agents.supervisor import SupervisorNode
from brief.assembler import assemble_brief, format_brief_text
from db.init_db import init_db
from hitl.actions import approve_draft, edit_and_approve, reject_draft, snooze_draft
from session.store import RunStateStore

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("nightshift")


def _verify_adk_graph() -> None:
    names = [a.name for a in root_agent.sub_agents]
    assert names == ["IngestionAgent", "TriageAgent", "ResponseAgent"], names


def cmd_dry_run() -> int:
    """Verify ADK graph topology (three sub-agents) without pipeline execution."""
    _verify_adk_graph()
    names = [a.name for a in root_agent.sub_agents]
    logger.info("ADK root_agent=%s sub_agents=%s", root_agent.name, names)
    logger.info("Dry run OK — ADK 2.0 graph wired.")
    return 0


def cmd_run_overnight(resume_run_id: str | None = None) -> int:
    init_db()
    _verify_adk_graph()

    if resume_run_id:
        run_state = RunStateStore.load(resume_run_id)
        if run_state is None:
            logger.error("Run %s not found — cannot resume", resume_run_id)
            return 1
        logger.info("Resuming run context for run_id=%s", resume_run_id)
    else:
        run_state = RunStateStore.start_run()

    supervisor = SupervisorNode(run_state=run_state)
    raw_items = supervisor.ingest_all()
    logger.info("Run %s — ingested %d items from MCP fixtures", run_state.run_id, len(raw_items))

    results = supervisor.run_batch(raw_items)
    snapshot = run_state.snapshot()

    for row in sorted(results, key=lambda r: (r["classified"].urgency_tier if r["classified"] else "ZZZ")):
        if row["error"]:
            logger.warning("  [%s] %s", row["raw_item_id"], row["error"])
            continue
        c, d = row["classified"], row["draft"]
        logger.info("  [%s] %s → draft %s status=%s", c.urgency_tier, row["raw_item_id"], d.id, d.status)

    hard = next((r for r in results if r["raw_item_id"] == "email-001"), None)
    if hard and hard["classified"]:
        assert hard["classified"].urgency_tier == "RED", "Hard case must classify RED"
        logger.info("Hard case email-001: RED ✓")

    logger.info(
        "Run %s complete — processed=%d failed=%d",
        snapshot["run_id"],
        snapshot["processed"],
        snapshot["failed"],
    )
    if snapshot["failed_items"]:
        logger.info("Failed items: %s", json.dumps(snapshot["failed_items"]))

    return 0


def cmd_morning_brief(*, as_json: bool = False) -> int:
    init_db()
    brief = assemble_brief()
    if as_json:
        print(json.dumps(brief.to_dict(), indent=2))
    else:
        print(format_brief_text(brief))
    return 0


def cmd_approve(draft_id: str, manager: str) -> int:
    init_db()
    draft = approve_draft(draft_id, manager)
    logger.info("Approved %s by %s at %s", draft.id, draft.approved_by, draft.approved_at)
    return 0


def cmd_edit_approve(draft_id: str, manager: str, draft_text: str) -> int:
    init_db()
    draft = edit_and_approve(draft_id, manager, draft_text)
    logger.info("Edit-approved %s by %s", draft.id, draft.approved_by)
    return 0


def cmd_reject(draft_id: str) -> int:
    init_db()
    draft = reject_draft(draft_id)
    logger.info("Rejected %s", draft.id)
    return 0


def cmd_snooze(draft_id: str) -> int:
    init_db()
    draft = snooze_draft(draft_id)
    logger.info("Snoozed %s", draft.id)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NightShift overnight agent pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Verify ADK graph only")
    parser.add_argument("--resume-run", metavar="RUN_ID", help="Reload prior overnight run context")

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("run-overnight", help="Ingest, classify, draft overnight batch")
    sub.add_parser("init-db", help="Create database tables")

    brief_parser = sub.add_parser("morning-brief", help="Show manager morning brief")
    brief_parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")

    approve_parser = sub.add_parser("approve", help="Approve a staged draft")
    approve_parser.add_argument("--draft-id", required=True)
    approve_parser.add_argument("--manager", required=True)

    edit_parser = sub.add_parser("edit-approve", help="Edit draft text then approve")
    edit_parser.add_argument("--draft-id", required=True)
    edit_parser.add_argument("--manager", required=True)
    edit_parser.add_argument("--text", required=True)

    reject_parser = sub.add_parser("reject", help="Reject a staged draft")
    reject_parser.add_argument("--draft-id", required=True)

    snooze_parser = sub.add_parser("snooze", help="Snooze a staged draft")
    snooze_parser.add_argument("--draft-id", required=True)

    args = parser.parse_args(argv)

    if args.dry_run:
        return cmd_dry_run()

    command = args.command or "run-overnight"

    if command == "init-db":
        init_db()
        logger.info("Database initialized.")
        return 0
    if command == "run-overnight":
        return cmd_run_overnight(resume_run_id=args.resume_run)
    if command == "morning-brief":
        return cmd_morning_brief(as_json=args.json)
    if command == "approve":
        return cmd_approve(args.draft_id, args.manager)
    if command == "edit-approve":
        return cmd_edit_approve(args.draft_id, args.manager, args.text)
    if command == "reject":
        return cmd_reject(args.draft_id)
    if command == "snooze":
        return cmd_snooze(args.draft_id)

    parser.error(f"Unknown command: {command}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
