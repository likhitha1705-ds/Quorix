-- Quorix Phase 2 schema. Idempotent: safe to run repeatedly, never drops data.

CREATE TABLE IF NOT EXISTS knowledge_sources (
    source_id        TEXT PRIMARY KEY,
    source_type      TEXT NOT NULL CHECK (source_type IN ('document', 'conversation', 'ticket')),
    name             TEXT NOT NULL,
    description      TEXT,
    authority_level  NUMERIC(3,2) NOT NULL CHECK (authority_level BETWEEN 0 AND 1),
    authority_basis  TEXT,
    ingestion_status TEXT NOT NULL DEFAULT 'never_ingested'
        CHECK (ingestion_status IN ('never_ingested', 'running', 'succeeded', 'partial', 'failed')),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS source_documents (
    document_id        TEXT PRIMARY KEY,
    source_id          TEXT NOT NULL REFERENCES knowledge_sources (source_id) ON DELETE CASCADE,
    original_record_id TEXT NOT NULL,
    source_type        TEXT NOT NULL CHECK (source_type IN ('document', 'conversation', 'ticket')),
    title              TEXT NOT NULL,
    description        TEXT,
    content_reference  TEXT NOT NULL,
    author             TEXT,
    status             TEXT,
    authority_level    NUMERIC(3,2) NOT NULL CHECK (authority_level BETWEEN 0 AND 1),
    authority_basis    TEXT,
    created_at         TIMESTAMPTZ,
    updated_at         TIMESTAMPTZ,
    ingested_at        TIMESTAMPTZ NOT NULL,
    metadata           JSONB NOT NULL DEFAULT '{}'::jsonb,
    content_hash       TEXT NOT NULL,
    index_fingerprint  TEXT,
    chunk_count        INTEGER NOT NULL DEFAULT 0,
    indexed_at         TIMESTAMPTZ,
    CONSTRAINT uq_source_original UNIQUE (source_id, original_record_id)
);
CREATE INDEX IF NOT EXISTS idx_source_documents_source ON source_documents (source_id);
CREATE INDEX IF NOT EXISTS idx_source_documents_type_updated ON source_documents (source_type, updated_at);

CREATE TABLE IF NOT EXISTS ingestion_jobs (
    job_id            UUID PRIMARY KEY,
    source_id         TEXT NOT NULL REFERENCES knowledge_sources (source_id) ON DELETE CASCADE,
    status            TEXT NOT NULL CHECK (status IN ('running', 'succeeded', 'partial', 'failed')),
    records_total     INTEGER NOT NULL DEFAULT 0,
    records_processed INTEGER NOT NULL DEFAULT 0,
    records_skipped   INTEGER NOT NULL DEFAULT 0,
    records_failed    INTEGER NOT NULL DEFAULT 0,
    started_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at      TIMESTAMPTZ,
    error_info        JSONB
);
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_source_started ON ingestion_jobs (source_id, started_at DESC);
