"""Ingestion orchestration: adapters -> chunks -> embeddings -> Qdrant + PostgreSQL.

Per-record failures are isolated and reported; they never produce a 'succeeded' job.
"""
from __future__ import annotations

import logging
from typing import Any, Protocol

from app.core.ids import sha256_text
from app.ingestion.base import SourceAdapter
from app.schemas.source import KnowledgeSource, RecordFailure, SourceRecord, SourceReport
from app.services.chunking import ChunkingService
from app.services.metadata_store import record_content_hash

log = logging.getLogger(__name__)
MAX_ERROR_CHARS = 500


class MetadataStoreLike(Protocol):
    def upsert_source(self, src: KnowledgeSource) -> None: ...
    def set_source_status(self, source_id: str, status: str) -> None: ...
    def start_job(self, source_id: str) -> str: ...
    def finish_job(self, report: SourceReport, error_info: dict[str, Any] | None = None) -> None: ...
    def get_index_state(self, document_id: str) -> dict[str, Any] | None: ...
    def upsert_document(self, rec: SourceRecord, content_hash: str) -> None: ...
    def mark_indexed(self, document_id: str, fingerprint: str, chunk_count: int) -> None: ...


class VectorStoreLike(Protocol):
    def delete_document(self, document_id: str) -> None: ...
    def upsert_chunks(self, chunks: list[Any], vectors: list[list[float]]) -> None: ...


class EmbedderLike(Protocol):
    model_name: str
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...


def _short(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {exc}"[:MAX_ERROR_CHARS]


class IngestionPipeline:
    def __init__(
        self,
        metadata: MetadataStoreLike,
        vectors: VectorStoreLike,
        embedder: EmbedderLike,
        chunker: ChunkingService,
    ) -> None:
        self.metadata = metadata
        self.vectors = vectors
        self.embedder = embedder
        self.chunker = chunker

    def _fingerprint(self, content_hash: str) -> str:
        """Changes when content, embedding model or chunking settings change."""
        return sha256_text(
            content_hash, self.embedder.model_name,
            str(self.chunker.chunk_size), str(self.chunker.chunk_overlap),
        )

    def run(self, adapters: list[SourceAdapter], force: bool = False) -> list[SourceReport]:
        return [self.run_source(a, force=force) for a in adapters]

    def run_source(self, adapter: SourceAdapter, force: bool = False) -> SourceReport:
        source = adapter.source_definition()
        report = SourceReport(source_id=source.source_id, source_type=source.source_type)
        self.metadata.upsert_source(source)
        self.metadata.set_source_status(source.source_id, "running")
        report.job_id = self.metadata.start_job(source.source_id)
        seen: set[str] = set()
        try:
            for result in adapter.iter_records():
                if result.error:
                    report.total += 1
                    report.failed += 1
                    report.failures.append(RecordFailure(reference=result.reference, error=result.error[:MAX_ERROR_CHARS]))
                    continue
                for record in result.records:
                    report.total += 1
                    if record.document_id in seen:
                        report.failed += 1
                        report.failures.append(RecordFailure(
                            reference=record.source_reference,
                            error=f"duplicate original_record_id {record.original_record_id!r}"))
                        continue
                    seen.add(record.document_id)
                    self._process_record(record, report, force)
        except Exception as exc:  # infrastructure-level failure: mark job failed, re-raise
            report.status = "failed"
            self.metadata.finish_job(report, {"fatal": _short(exc), **(
                {"failures": [f.model_dump() for f in report.failures]} if report.failures else {})})
            self.metadata.set_source_status(source.source_id, "failed")
            raise
        if report.failed == 0:
            report.status = "succeeded"
        elif report.processed + report.skipped > 0:
            report.status = "partial"
        else:
            report.status = "failed"
        self.metadata.finish_job(report)
        self.metadata.set_source_status(source.source_id, report.status)
        return report

    def _process_record(self, record: SourceRecord, report: SourceReport, force: bool) -> None:
        try:
            content_hash = record_content_hash(record)
            fingerprint = self._fingerprint(content_hash)
            if not force:
                state = self.metadata.get_index_state(record.document_id)
                if state and state["indexed_at"] and state["index_fingerprint"] == fingerprint:
                    report.skipped += 1
                    return
            chunks = self.chunker.chunk_record(record)
            if not chunks:
                raise ValueError("record produced no chunks")
            self.metadata.upsert_document(record, content_hash)  # marks as not indexed
            vectors = self.embedder.embed_documents([c.embedding_text() for c in chunks])
            self.vectors.delete_document(record.document_id)
            self.vectors.upsert_chunks(chunks, vectors)
            self.metadata.mark_indexed(record.document_id, fingerprint, len(chunks))
            report.processed += 1
            report.chunks += len(chunks)
        except Exception as exc:  # noqa: BLE001 - recorded in the report
            log.warning("Record %s failed: %s", record.source_reference, exc)
            report.failed += 1
            report.failures.append(RecordFailure(reference=record.source_reference, error=_short(exc)))
