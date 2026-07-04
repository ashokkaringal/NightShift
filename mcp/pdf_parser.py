"""Extract plain text from machine-readable PDFs for MCP ingestion."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

DEFAULT_MAX_CHARS = 12_000

_EMPTY_PAGE_WARN = "[PDF text extraction unavailable: scanned or image-only PDF]"


class PdfExtractionStatus(str, Enum):
    OK = "ok"
    EMPTY = "empty"
    ERROR = "error"


@dataclass(frozen=True)
class PdfExtractionResult:
    path: Path
    text: str
    page_count: int
    status: PdfExtractionStatus
    warnings: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return self.status == PdfExtractionStatus.OK and bool(self.text.strip())


def normalize_pdf_text(text: str, *, max_chars: int = DEFAULT_MAX_CHARS) -> str:
    """Collapse whitespace and cap length for downstream LLM prompts."""
    collapsed = re.sub(r"[ \t]+", " ", text)
    collapsed = re.sub(r"\n{3,}", "\n\n", collapsed)
    collapsed = collapsed.strip()
    if len(collapsed) > max_chars:
        collapsed = collapsed[:max_chars].rstrip() + "\n[... truncated ...]"
    return collapsed


def extract_pdf_text(path: Path | str, *, max_chars: int = DEFAULT_MAX_CHARS) -> PdfExtractionResult:
    """Extract text from a PDF file. Does not log file contents."""
    pdf_path = Path(path)
    if not pdf_path.is_file():
        return PdfExtractionResult(
            path=pdf_path,
            text="",
            page_count=0,
            status=PdfExtractionStatus.ERROR,
            warnings=(f"file not found: {pdf_path.name}",),
        )

    try:
        from pypdf import PdfReader
    except ImportError as exc:
        return PdfExtractionResult(
            path=pdf_path,
            text="",
            page_count=0,
            status=PdfExtractionStatus.ERROR,
            warnings=(f"pypdf not installed: {exc}",),
        )

    try:
        reader = PdfReader(str(pdf_path))
        page_count = len(reader.pages)
        parts: list[str] = []
        for page in reader.pages:
            chunk = page.extract_text() or ""
            if chunk.strip():
                parts.append(chunk)
        raw = "\n\n".join(parts)
        normalized = normalize_pdf_text(raw, max_chars=max_chars)
        if not normalized:
            return PdfExtractionResult(
                path=pdf_path,
                text=_EMPTY_PAGE_WARN,
                page_count=page_count,
                status=PdfExtractionStatus.EMPTY,
                warnings=("no extractable text (likely scanned/image-only)",),
            )
        return PdfExtractionResult(
            path=pdf_path,
            text=normalized,
            page_count=page_count,
            status=PdfExtractionStatus.OK,
        )
    except Exception as exc:
        return PdfExtractionResult(
            path=pdf_path,
            text="",
            page_count=0,
            status=PdfExtractionStatus.ERROR,
            warnings=(f"parse error: {type(exc).__name__}",),
        )


_ATTACHMENT_BLOCK_RE = re.compile(
    r"\n\n\[Attachment:\s*([^\]]+)\]\n(.*?)(?=\n\n\[Attachment:\s*|\Z)",
    re.DOTALL,
)


def split_body_and_attachments(merged_text: str) -> tuple[str, list[dict[str, str]]]:
    """Split merged raw_text into email body and structured attachment entries."""
    attachments = [
        {
            "filename": match.group(1).strip(),
            "text": match.group(2).strip(),
            "kind": "pdf",
        }
        for match in _ATTACHMENT_BLOCK_RE.finditer(merged_text)
    ]
    body = _ATTACHMENT_BLOCK_RE.sub("", merged_text).strip()
    return body, attachments


def format_attachment_block(filename: str, extracted_text: str) -> str:
    """Delimited block appended to email raw_text."""
    body = extracted_text.strip() or _EMPTY_PAGE_WARN
    return f"\n\n[Attachment: {filename}]\n{body}"


def resolve_attachment_path(fixtures_root: Path, attachment_path: str) -> Path:
    """Resolve attachment path relative to fixtures root."""
    candidate = fixtures_root / attachment_path
    if candidate.is_file():
        return candidate
    return fixtures_root / "attachments" / Path(attachment_path).name
