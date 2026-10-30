"""Seed script to populate initial knowledge sources in PostgreSQL."""
from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.core.config import get_settings
from app.db.postgres import connect, run_migrations
from app.intelligence.source_registry import DEFAULT_SOURCE_TOPICS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger("seed_data")

INITIAL_SOURCES = [
    {
        "source_id": "src_documents",
        "source_type": "document",
        "name": "Technical Documents",
        "description": "Technical documentation: architecture, API and configuration references, guidelines, specifications, system design.",
        "authority_level": 0.85,
        "authority_basis": "approved documentation is highly authoritative",
        "supported_topics": DEFAULT_SOURCE_TOPICS["document"],
    },
    {
        "source_id": "src_conversations",
        "source_type": "conversation",
        "name": "Engineering Conversations",
        "description": "Engineering discussions, design decisions, architectural history, team debates, and debugging threads.",
        "authority_level": 0.50,
        "authority_basis": "informal discussion unless marked as a decision",
        "supported_topics": DEFAULT_SOURCE_TOPICS["conversation"],
    },
    {
        "source_id": "src_tickets",
        "source_type": "ticket",
        "name": "Development Tickets",
        "description": "Bug reports, feature requests, implementation tasks, issue tracking, and resolutions.",
        "authority_level": 0.60,
        "authority_basis": "depends on ticket status",
        "supported_topics": DEFAULT_SOURCE_TOPICS["ticket"],
    },
]


def seed() -> None:
    settings = get_settings()
    if not settings.database_url:
        log.warning("DATABASE_URL not configured. Skipping PostgreSQL seed.")
        return

    log.info("Connecting to PostgreSQL and running migrations...")
    with connect() as conn:
        applied = run_migrations(conn)
        log.info("Applied %d migration(s): %s", len(applied), applied)

        with conn.transaction():
            for src in INITIAL_SOURCES:
                conn.execute(
                    """INSERT INTO knowledge_sources
                       (source_id, source_type, name, description, authority_level,
                        authority_basis, supported_topics, updated_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, now())
                       ON CONFLICT (source_id) DO UPDATE SET
                         source_type = EXCLUDED.source_type,
                         name = EXCLUDED.name,
                         description = EXCLUDED.description,
                         authority_level = EXCLUDED.authority_level,
                         authority_basis = EXCLUDED.authority_basis,
                         supported_topics = EXCLUDED.supported_topics,
                         updated_at = now()""",
                    (
                        src["source_id"],
                        src["source_type"],
                        src["name"],
                        src["description"],
                        src["authority_level"],
                        src["authority_basis"],
                        src["supported_topics"],
                    ),
                )
                log.info("Upserted source %s (%s)", src["source_id"], src["name"])

    log.info("Knowledge sources seeding complete.")


if __name__ == "__main__":
    seed()

