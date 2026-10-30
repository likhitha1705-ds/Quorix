"""Source Registry service: reads knowledge source metadata stored in PostgreSQL."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import psycopg

from app.core.config import get_settings
from app.db.postgres import connect
from app.schemas.intelligence import SourceMetadata

log = logging.getLogger(__name__)

# Default topics per source type used when not populated or for local fallback
DEFAULT_SOURCE_TOPICS: dict[str, list[str]] = {
    "document": [
        "architecture", "specifications", "configuration", "api",
        "guidelines", "design", "setup", "reference", "documentation",
        "chunking", "embedding", "vector", "pipeline", "redis", "caching",
        "cache", "ttl", "deployment", "deploy", "runbook", "canary", "rollout",
        "devops", "ci/cd", "argocd", "authentication", "auth", "security",
        "oauth", "jwt", "oidc", "database", "sharding", "postgres", "postgresql",
        "scaling", "storage", "infrastructure", "pgbouncer", "sla", "latency",
    ],
    "conversation": [
        "decisions", "discussions", "history", "reasons", "debugging",
        "tradeoffs", "why", "rationale", "team", "meeting", "redis", "caching",
        "cache", "ttl", "deployment", "deploy", "canary", "rollout", "migration",
        "architecture", "slack", "incident", "postmortem", "backend", "devops",
        "auth", "sharding", "database",
    ],
    "ticket": [
        "bugs", "issues", "fixes", "features", "tasks", "implementation",
        "tickets", "resolutions", "errors", "timeout", "regression", "incident",
        "proj", "redis", "caching", "performance", "benchmark", "jira", "github",
        "deploy", "canary", "auth", "database", "sharding",
    ],
}


class SourceRegistryService:
    """Reads source metadata from PostgreSQL, with fallback to standard sources."""

    def __init__(self, conn: psycopg.Connection | None = None) -> None:
        self._conn = conn

    def get_available_sources(self) -> list[SourceMetadata]:
        """Fetch available knowledge sources from PostgreSQL or fallback if unavailable."""
        if self._conn is not None:
            return self._fetch_from_connection(self._conn)

        settings = get_settings()
        if settings.database_url:
            try:
                with connect() as conn:
                    return self._fetch_from_connection(conn)
            except Exception as exc:
                log.warning("PostgreSQL connection failed (%s); falling back to default source registry", exc)

        return self.get_default_sources()

    def _fetch_from_connection(self, conn: psycopg.Connection) -> list[SourceMetadata]:
        """Execute query to read source metadata from PostgreSQL."""
        # Determine if supported_topics column exists
        has_topics_col = False
        try:
            res = conn.execute(
                """SELECT column_name FROM information_schema.columns
                   WHERE table_name = 'knowledge_sources' AND column_name = 'supported_topics'"""
            ).fetchone()
            has_topics_col = res is not None
        except Exception:
            has_topics_col = False

        query = (
            """SELECT source_id, source_type, name, description, authority_level, updated_at,
                      COALESCE(supported_topics, '{}') AS supported_topics
               FROM knowledge_sources"""
            if has_topics_col
            else """SELECT source_id, source_type, name, description, authority_level, updated_at
                    FROM knowledge_sources"""
        )

        rows = conn.execute(query).fetchall()
        if not rows:
            log.info("No sources found in knowledge_sources table; returning default sources")
            return self.get_default_sources()

        sources: list[SourceMetadata] = []
        for r in rows:
            stype = str(r["source_type"]).lower()
            topics = r.get("supported_topics")
            if not topics:
                topics = DEFAULT_SOURCE_TOPICS.get(stype, [])

            sources.append(
                SourceMetadata(
                    source_id=r["source_id"],
                    source_name=r["name"],
                    source_type=stype,
                    description=r["description"] or "",
                    authority_score=float(r["authority_level"]),
                    last_updated=r["updated_at"] or datetime.now(timezone.utc),
                    supported_topics=list(topics),
                )
            )
        return sources

    @staticmethod
    def get_default_sources() -> list[SourceMetadata]:
        """Return the default Quorix source metadata for local development or testing."""
        now = datetime.now(timezone.utc)
        return [
            SourceMetadata(
                source_id="src_documents",
                source_name="Technical Documents",
                source_type="document",
                description="Technical documentation: architecture, API and configuration references, guidelines, specifications, system design.",
                authority_score=0.85,
                last_updated=now,
                supported_topics=DEFAULT_SOURCE_TOPICS["document"],
            ),
            SourceMetadata(
                source_id="src_conversations",
                source_name="Engineering Conversations",
                source_type="conversation",
                description="Engineering discussions, design decisions, architectural history, team debates, and debugging threads.",
                authority_score=0.50,
                last_updated=now,
                supported_topics=DEFAULT_SOURCE_TOPICS["conversation"],
            ),
            SourceMetadata(
                source_id="src_tickets",
                source_name="Development Tickets",
                source_type="ticket",
                description="Bug reports, feature requests, implementation tasks, issue tracking, and resolutions.",
                authority_score=0.60,
                last_updated=now,
                supported_topics=DEFAULT_SOURCE_TOPICS["ticket"],
            ),
        ]

