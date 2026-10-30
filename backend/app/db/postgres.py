"""PostgreSQL (Supabase) access via psycopg 3, plus idempotent migrations."""
from __future__ import annotations

import logging
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from app.core.config import get_settings

log = logging.getLogger(__name__)
MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def connect(dsn: str | None = None) -> psycopg.Connection:
    """Open a connection. prepare_threshold=None keeps it compatible with
    Supabase's pgbouncer (transaction pooling) endpoints."""
    dsn = dsn or get_settings().require_database_url()
    return psycopg.connect(dsn, row_factory=dict_row, prepare_threshold=None)


def run_migrations(conn: psycopg.Connection) -> list[str]:
    """Apply any not-yet-applied .sql files in order. Returns applied versions."""
    applied: list[str] = []
    with conn.transaction():
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            "version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
        )
    done = {r["version"] for r in conn.execute("SELECT version FROM schema_migrations")}
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        if path.stem in done:
            continue
        with conn.transaction():
            conn.execute(path.read_text(encoding="utf-8"))
            conn.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (path.stem,))
        applied.append(path.stem)
        log.info("Applied migration %s", path.stem)
    return applied
