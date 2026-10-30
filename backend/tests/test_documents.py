import pytest

from app.ingestion.base import RecordValidationError
from app.ingestion.documents import DocumentAdapter, parse_front_matter
from tests.conftest import minimal_pdf

MD = """---
id: DOC-X
title: Cache Guide
author: Ann
created_at: 2026-01-01T00:00:00Z
updated_at: 2026-02-01T00:00:00Z
status: approved
tags: [redis, cache]
---
# Cache Guide

Intro text.

## TTL
The TTL is 300 seconds.
"""


def adapter(d):
    return DocumentAdapter(d, max_bytes=10_000)


def test_front_matter_parse():
    meta, body = parse_front_matter(MD)
    assert meta["id"] == "DOC-X" and meta["tags"] == ["redis", "cache"]
    assert body.lstrip().startswith("# Cache Guide")


def test_markdown_parsing_preserves_metadata(data_dir):
    (data_dir / "documents" / "guide.md").write_text(MD, encoding="utf-8")
    [rec] = adapter(data_dir).parse(data_dir / "documents" / "guide.md")
    assert rec.original_record_id == "DOC-X" and rec.title == "Cache Guide"
    assert rec.author == "Ann" and rec.status == "approved"
    assert rec.authority_level == 0.9 and rec.source_reference == "documents/guide.md"
    assert rec.metadata["filename"] == "guide.md" and rec.metadata["tags"] == ["redis", "cache"]
    assert [s.label for s in rec.segments] == ["Cache Guide", "Cache Guide > TTL"]


def test_txt_without_front_matter_uses_filename(data_dir):
    p = data_dir / "documents" / "notes.txt"
    p.write_text("First paragraph.\n\nSecond paragraph.", encoding="utf-8")
    [rec] = adapter(data_dir).parse(p)
    assert rec.original_record_id == "notes" and rec.title == "notes"
    assert len(rec.segments) == 2 and rec.created_at is None


def test_pdf_extraction_and_sidecar(data_dir):
    p = data_dir / "documents" / "spec.pdf"
    p.write_bytes(minimal_pdf("Hello PDF world"))
    (data_dir / "documents" / "spec.pdf.meta.json").write_text('{"id": "PDF-1", "title": "Spec"}')
    [rec] = adapter(data_dir).parse(p)
    assert "Hello PDF world" in rec.content
    assert rec.original_record_id == "PDF-1" and rec.title == "Spec"
    assert rec.segments[0].label == "page 1" and rec.metadata["file_type"] == "pdf"


@pytest.mark.parametrize("name,data", [("empty.md", b""), ("bad.txt", b"\xff\xfe\x00\x80\x81"),
                                       ("broken.pdf", b"not a pdf"), ("big.txt", b"x" * 20_000)])
def test_invalid_files_rejected(data_dir, name, data):
    p = data_dir / "documents" / name
    p.write_bytes(data)
    with pytest.raises(RecordValidationError):
        adapter(data_dir).parse(p)


def test_iter_records_reports_failures_without_aborting(data_dir):
    (data_dir / "documents" / "ok.md").write_text("# T\n\nbody", encoding="utf-8")
    (data_dir / "documents" / "empty.md").write_bytes(b"")
    results = list(adapter(data_dir).iter_records())
    assert sum(1 for r in results if r.error) == 1 and sum(len(r.records) for r in results) == 1
