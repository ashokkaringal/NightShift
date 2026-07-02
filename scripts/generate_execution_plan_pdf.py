#!/usr/bin/env python3
"""Convert NightShift execution plan markdown to a styled PDF."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PLAN = "NightShift_Execution_Plan-V7.4.md"
CSS_FILE = Path(__file__).resolve().parent / "pdf" / "nightshift-plan.css"
BUILD_DIR = Path(__file__).resolve().parent / "pdf"
HTML_FILE = BUILD_DIR / "_build.html"

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    shutil.which("google-chrome") or "",
    shutil.which("chromium") or "",
]


def plan_paths(stem: str) -> tuple[Path, Path]:
    md = ROOT / f"{stem}.md" if not stem.endswith(".md") else ROOT / stem
    pdf = md.with_suffix(".pdf")
    return md, pdf


def find_chrome() -> str:
    for candidate in CHROME_CANDIDATES:
        if candidate and Path(candidate).exists():
            return candidate
    raise RuntimeError("Chrome/Chromium not found — required for PDF generation.")


def run_pandoc(md_file: Path) -> None:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [
        "pandoc",
        str(md_file),
        "-f",
        "markdown+pipe_tables+fenced_code_blocks+backtick_code_blocks+task_lists+strikeout+tex_math_dollars",
        "-t",
        "html5",
        "--standalone",
        "--toc",
        "--toc-depth=3",
        "--number-sections",
        f"--css={CSS_FILE}",
        "--embed-resources",
        "--syntax-highlighting=pygments",
        "--metadata",
        "title=NightShift — Execution Plan (V7.4)",
        "--metadata",
        "subtitle=Google & Kaggle 5-Day AI Agents Intensive (Vibe Coding) — Capstone Track: Agents for Business",
        "--metadata",
        "author=NightShift Team (Members A, B, C, D)",
        "--metadata",
        "date=July 2026",
        "-o",
        str(HTML_FILE),
    ]
    subprocess.run(cmd, check=True, cwd=ROOT)


def run_chrome_pdf(chrome: str, out_pdf: Path) -> None:
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=15000",
        f"--print-to-pdf={out_pdf}",
        HTML_FILE.resolve().as_uri(),
    ]
    subprocess.run(cmd, check=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate styled PDF from execution plan markdown")
    parser.add_argument(
        "--input",
        default=DEFAULT_PLAN,
        help=f"Markdown file name in repo root (default: {DEFAULT_PLAN})",
    )
    args = parser.parse_args(argv)

    md_file, out_pdf = plan_paths(args.input)
    if not md_file.exists():
        print(f"Missing markdown file: {md_file}", file=sys.stderr)
        return 1
    if not shutil.which("pandoc"):
        print("pandoc is required but not installed.", file=sys.stderr)
        return 1

    print(f"Converting: {md_file.name}")
    run_pandoc(md_file)
    print(f"HTML built: {HTML_FILE}")

    chrome = find_chrome()
    print(f"Rendering PDF via: {chrome}")
    run_chrome_pdf(chrome, out_pdf)

    size_kb = out_pdf.stat().st_size / 1024
    print(f"PDF written: {out_pdf} ({size_kb:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
