"""Deterministic identifiers so re-ingestion is idempotent."""
from __future__ import annotations

import hashlib
import uuid

_NAMESPACE = uuid.UUID("6f1c2f1e-5b7a-4c1d-9a55-0d6f4b6a1e01")


def make_document_id(source_type: str, original_record_id: str) -> str:
    return f"{source_type}:{original_record_id}"


def make_chunk_id(document_id: str, chunk_index: int) -> str:
    return f"{document_id}#c{chunk_index:04d}"


def chunk_point_id(chunk_id: str) -> str:
    """Qdrant point IDs must be UUIDs or ints; derive a stable UUID from the chunk ID."""
    return str(uuid.uuid5(_NAMESPACE, chunk_id))


def sha256_text(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode("utf-8"))
        h.update(b"\x1f")
    return h.hexdigest()
