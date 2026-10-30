"""Document adapter: PDF, Markdown and TXT.

Markdown/TXT files may start with a simple front matter block (``key: value`` lines
between ``---`` markers). Any file may also have an optional ``<file>.meta.json``
sidecar (useful for PDFs); sidecar values override front matter.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.core.config import get_settings
from app.core.text import normalize_text
from app.ingestion.authority import SOURCE_DEFAULTS, resolve_authority
from app.ingestion.base import RecordValidationError, SourceAdapter
from app.schemas.source import KnowledgeSource, SourceRecord, SourceType, TextSegment

log = logging.getLogger(__name__)

SUPPORTED = {".pdf", ".md", ".markdown", ".txt"}
_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_RESERVED = {
    "id", "title", "author", "created_at", "updated_at", "status",
    "description", "authority_level",
}


def parse_front_matter(text: str) -> tuple[dict[str, Any], str]:
    lines = text.replace("\r\n", "\n").split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, text
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return {}, text
    meta: dict[str, Any] = {}
    for ln in lines[1:end]:
        if ":" not in ln or ln.lstrip().startswith("#"):
            continue
        key, _, val = ln.partition(":")
        val = val.strip().strip("'\"")
        if val.startswith("[") and val.endswith("]"):
            meta[key.strip()] = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
        else:
            meta[key.strip()] = val
    return meta, "\n".join(lines[end + 1 :])


def split_markdown_sections(body: str) -> list[TextSegment]:
    """One segment per heading section; label is the heading path."""
    sections: list[tuple[str, list[str]]] = []
    path: list[tuple[int, str]] = []
    current: tuple[str, list[str]] = ("", [])
    in_code = False
    for line in body.split("\n"):
        if line.strip().startswith("```"):
            in_code = not in_code
        m = None if in_code else _HEADING.match(line)
        if m:
            if "\n".join(current[1]).strip():
                sections.append(current)
            level = len(m.group(1))
            path = [p for p in path if p[0] < level] + [(level, m.group(2))]
            current = (" > ".join(p[1] for p in path), [line])
        else:
            current[1].append(line)
    if "\n".join(current[1]).strip():
        sections.append(current)
    return [
        TextSegment(text=normalize_text("\n".join(lines)), label=label or None)
        for label, lines in sections
        if normalize_text("\n".join(lines))
    ]


def split_paragraphs(body: str) -> list[TextSegment]:
    return [
        TextSegment(text=p)
        for p in (normalize_text(x) for x in re.split(r"\n\s*\n", body))
        if p
    ]


class DocumentAdapter(SourceAdapter):
    source_type = SourceType.DOCUMENT
    default_source_id = "src_documents"

    def __init__(self, data_dir: Path, source_id: str | None = None,
                 max_bytes: int | None = None) -> None:
        super().__init__(data_dir, source_id)
        self.max_bytes = max_bytes or get_settings().max_document_bytes

    def source_definition(self) -> KnowledgeSource:
        return KnowledgeSource(
            source_id=self.source_id,
            source_type=self.source_type,
            name="Technical Documents",
            description="Technical documentation: architecture, API and configuration references, guidelines.",
            authority_level=SOURCE_DEFAULTS[self.source_type],
            authority_basis="approved documentation is highly authoritative",
        )

    def discover(self) -> list[Path]:
        root = self.data_dir / "documents"
        return sorted(p for p in root.glob("*") if p.is_file() and p.suffix.lower() in SUPPORTED)

    def parse(self, path: Path) -> list[SourceRecord]:
        size = path.stat().st_size
        if size == 0:
            raise RecordValidationError("file is empty")
        if size > self.max_bytes:
            raise RecordValidationError(f"file too large ({size} bytes > {self.max_bytes})")
        ext = path.suffix.lower()
        meta: dict[str, Any] = {}
        if ext == ".pdf":
            segments, pdf_meta = self._read_pdf(path)
            meta.update(pdf_meta)
        else:
            try:
                raw = path.read_text(encoding="utf-8-sig")
            except UnicodeDecodeError as exc:
                raise RecordValidationError(f"not valid UTF-8 text: {exc}") from exc
            fm, body = parse_front_matter(raw)
            meta.update(fm)
            segments = (
                split_markdown_sections(body) if ext in {".md", ".markdown"} else split_paragraphs(body)
            )
        sidecar = path.with_name(path.name + ".meta.json")
        if sidecar.exists():
            try:
                meta.update(json.loads(sidecar.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError) as exc:
                raise RecordValidationError(f"invalid sidecar {sidecar.name}: {exc}") from exc
        if not segments:
            raise RecordValidationError("no extractable text")

        content = "\n\n".join(s.text for s in segments)
        title = (
            meta.get("title")
            or next((s.text.lstrip("# ").split("\n")[0] for s in segments if s.text.startswith("# ")), None)
            or path.stem
        )
        status = str(meta["status"]).lower() if meta.get("status") else None
        explicit = float(meta["authority_level"]) if meta.get("authority_level") else None
        extra = {k: v for k, v in meta.items() if k not in _RESERVED}
        extra.update({"filename": path.name, "file_type": ext.lstrip("."), "size_bytes": size})
        level, basis = resolve_authority(self.source_type, status, extra, explicit)
        try:
            return [
                SourceRecord(
                    source_id=self.source_id,
                    source_type=self.source_type,
                    original_record_id=str(meta.get("id") or path.stem),
                    title=str(title),
                    content=content,
                    description=meta.get("description"),
                    source_reference=self.relative_reference(path),
                    author=meta.get("author"),
                    status=status,
                    created_at=_parse_dt(meta.get("created_at")),
                    updated_at=_parse_dt(meta.get("updated_at")),
                    authority_level=level,
                    authority_basis=basis,
                    metadata=extra,
                    segments=segments,
                )
            ]
        except ValidationError as exc:
            raise RecordValidationError(str(exc)) from exc

    @staticmethod
    def _read_pdf(path: Path) -> tuple[list[TextSegment], dict[str, Any]]:
        from pypdf import PdfReader  # imported lazily; only needed for PDFs
        from pypdf.errors import PyPdfError

        try:
            reader = PdfReader(str(path))
            if reader.is_encrypted:
                raise RecordValidationError("PDF is encrypted")
            segments = []
            for n, page in enumerate(reader.pages, start=1):
                text = normalize_text(page.extract_text() or "")
                if text:
                    segments.append(TextSegment(text=text, label=f"page {n}"))
            info = reader.metadata
            meta: dict[str, Any] = {"page_count": len(reader.pages)}
            if info and info.title:
                meta["title"] = str(info.title)
            if info and info.author:
                meta["author"] = str(info.author)
            if not segments:
                raise RecordValidationError("PDF has no extractable text (scanned?)")
            return segments, meta
        except RecordValidationError:
            raise
        except (PyPdfError, OSError, ValueError) as exc:
            raise RecordValidationError(f"cannot read PDF: {exc}") from exc


def _parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise RecordValidationError(f"invalid timestamp {value!r}") from exc
