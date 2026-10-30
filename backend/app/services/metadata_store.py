"""Relational persistence for the source registry, original records and ingestion jobs."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from app.core.ids import sha256_text
from app.schemas.source import KnowledgeSource, SourceRecord, SourceReport


def record_content_hash(record: SourceRecord) -> str:
    """Hash of everything that affects the indexed output of a record."""
    return sha256_text(
        record.title,
        record.content,
        record.status or "",
        str(record.created_at),
        str(record.updated_at),
        f"{record.authority_level:.2f}",
        record.source_reference,
    )


class MetadataStore:
    """Holds one reusable connection for the duration of an ingestion run."""

    def __init__(self, conn: psycopg.Connection) -> None:
        self.conn = conn

    def upsert_source(self, src: KnowledgeSource) -> None:
        with self.conn.transaction():
            self.conn.execute(
                """INSERT INTO knowledge_sources
                   (source_id, source_type, name, description, authority_level, authority_basis)
                   VALUES (%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (source_id) DO UPDATE SET
                     source_type=EXCLUDED.source_type, name=EXCLUDED.name,
                     description=EXCLUDED.description, authority_level=EXCLUDED.authority_level,
                     authority_basis=EXCLUDED.authority_basis, updated_at=now()""",
                (src.source_id, src.source_type.value, src.name, src.description,
                 src.authority_level, src.authority_basis),
            )

    def set_source_status(self, source_id: str, status: str) -> None:
        with self.conn.transaction():
            self.conn.execute(
                "UPDATE knowledge_sources SET ingestion_status=%s, updated_at=now() WHERE source_id=%s",
                (status, source_id),
            )

    def start_job(self, source_id: str) -> str:
        job_id = str(uuid.uuid4())
        with self.conn.transaction():
            self.conn.execute(
                "INSERT INTO ingestion_jobs (job_id, source_id, status) VALUES (%s,%s,'running')",
                (job_id, source_id),
            )
        return job_id

    def finish_job(self, report: SourceReport, error_info: dict[str, Any] | None = None) -> None:
        info = error_info if error_info is not None else (
            {"failures": [f.model_dump() for f in report.failures]} if report.failures else None
        )
        with self.conn.transaction():
            self.conn.execute(
                """UPDATE ingestion_jobs SET status=%s, records_total=%s, records_processed=%s,
                   records_skipped=%s, records_failed=%s, completed_at=%s, error_info=%s
                   WHERE job_id=%s""",
                (report.status, report.total, report.processed, report.skipped, report.failed,
                 datetime.now(timezone.utc), Jsonb(info) if info else None, report.job_id),
            )

    def get_index_state(self, document_id: str) -> dict[str, Any] | None:
        return self.conn.execute(
            "SELECT index_fingerprint, indexed_at FROM source_documents WHERE document_id=%s",
            (document_id,),
        ).fetchone()

    def upsert_document(self, rec: SourceRecord, content_hash: str) -> None:
        """Insert/update the record and mark it as not yet indexed."""
        with self.conn.transaction():
            self.conn.execute(
                """INSERT INTO source_documents
                   (document_id, source_id, original_record_id, source_type, title, description,
                    content_reference, author, status, authority_level, authority_basis,
                    created_at, updated_at, ingested_at, metadata, content_hash,
                    index_fingerprint, chunk_count, indexed_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NULL,0,NULL)
                   ON CONFLICT (document_id) DO UPDATE SET
                     title=EXCLUDED.title, description=EXCLUDED.description,
                     content_reference=EXCLUDED.content_reference, author=EXCLUDED.author,
                     status=EXCLUDED.status, authority_level=EXCLUDED.authority_level,
                     authority_basis=EXCLUDED.authority_basis, created_at=EXCLUDED.created_at,
                     updated_at=EXCLUDED.updated_at, ingested_at=EXCLUDED.ingested_at,
                     metadata=EXCLUDED.metadata, content_hash=EXCLUDED.content_hash,
                     index_fingerprint=NULL, chunk_count=0, indexed_at=NULL""",
                (rec.document_id, rec.source_id, rec.original_record_id, rec.source_type.value,
                 rec.title, rec.description, rec.source_reference, rec.author, rec.status,
                 rec.authority_level, rec.authority_basis, rec.created_at, rec.updated_at,
                 rec.ingestion_timestamp, Jsonb(rec.metadata), content_hash),
            )

    def mark_indexed(self, document_id: str, fingerprint: str, chunk_count: int) -> None:
        with self.conn.transaction():
            self.conn.execute(
                "UPDATE source_documents SET index_fingerprint=%s, chunk_count=%s, indexed_at=now() "
                "WHERE document_id=%s",
                (fingerprint, chunk_count, document_id),
            )

    def count_documents(self, source_id: str | None = None) -> int:
        if source_id:
            row = self.conn.execute(
                "SELECT count(*) AS n FROM source_documents WHERE source_id=%s", (source_id,)
            ).fetchone()
        else:
            row = self.conn.execute("SELECT count(*) AS n FROM source_documents").fetchone()
        return int(row["n"])
