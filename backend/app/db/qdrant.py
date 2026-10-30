"""Qdrant client factory."""
from __future__ import annotations

import logging
from qdrant_client import QdrantClient

from app.core.config import get_settings

log = logging.getLogger(__name__)

_shared_memory_client: QdrantClient | None = None


def get_qdrant_client() -> QdrantClient:
    url, api_key = get_settings().require_qdrant()
    return QdrantClient(url=url, api_key=api_key, timeout=30)


def get_shared_qdrant_client() -> QdrantClient:
    """Return a shared singleton QdrantClient.
    
    If QDRANT_URL is configured, attempts connection to cluster.
    Otherwise, returns an in-memory instance persisted across requests in the current process.
    """
    global _shared_memory_client
    settings = get_settings()

    if settings.qdrant_url:
        try:
            return get_qdrant_client()
        except Exception as exc:
            log.warning("Could not connect to Qdrant cluster (%s); falling back to shared in-memory instance", exc)

    if _shared_memory_client is None:
        _shared_memory_client = QdrantClient(":memory:")
    return _shared_memory_client
