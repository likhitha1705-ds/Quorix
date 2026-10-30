"""End-to-end check against a real (embedded) PostgreSQL and Qdrant local mode.
Skipped unless `pgserver` is installed (pip install pgserver). Uses a fake embedder,
so it needs no model download and no cloud credentials."""
import hashlib
import tempfile

import pytest

pgserver = pytest.importorskip("pgserver")

from qdrant_client import QdrantClient  # noqa: E402
from qdrant_client.http import models as qm  # noqa: E402

from app.db.postgres import connect, run_migrations  # noqa: E402
from app.ingestion.conversations import ConversationAdapter  # noqa: E402
from app.ingestion.documents import DocumentAdapter  # noqa: E402
from app.ingestion.pipeline import IngestionPipeline  # noqa: E402
from app.ingestion.tickets import TicketAdapter  # noqa: E402
from app.services.chunking import ChunkingService  # noqa: E402
from app.services.metadata_store import MetadataStore  # noqa: E402
from app.services.vector_store import VectorDimensionMismatch, VectorStore  # noqa: E402
from tests.conftest import REPO_DATA  # noqa: E402

DIM = 16


class HashEmbedder:
    model_name = "hash-embedder"

    def embed_documents(self, texts):
        return [[b / 255 for b in hashlib.sha256(t.encode()).digest()[:DIM]] for t in texts]


@pytest.fixture(scope="module")
def env():
    srv = pgserver.get_server(tempfile.mkdtemp(), cleanup_mode="stop")
    conn = connect(srv.get_uri())
    qc = QdrantClient(":memory:")
    yield conn, VectorStore(qc, "test_chunks"), qc
    conn.close()
    srv.cleanup()


def adapters():
    return [DocumentAdapter(REPO_DATA), ConversationAdapter(REPO_DATA), TicketAdapter(REPO_DATA)]


def test_migrations_are_idempotent(env):
    conn, _, _ = env
    assert run_migrations(conn) == ["001_init"]
    assert run_migrations(conn) == []


def test_full_ingestion_and_rerun_has_no_duplicates(env):
    conn, store, qc = env
    store.ensure_collection(DIM)
    pipe = IngestionPipeline(MetadataStore(conn), store, HashEmbedder(), ChunkingService(500, 80))
    first = pipe.run(adapters())
    assert [r.status for r in first] == ["succeeded"] * 3
    points, docs = store.count(), MetadataStore(conn).count_documents()
    assert docs == 40 and points == sum(r.chunks for r in first) > 40

    second = pipe.run(adapters())
    assert all(r.processed == 0 for r in second) and sum(r.skipped for r in second) == 40
    forced = pipe.run(adapters(), force=True)
    assert sum(r.processed for r in forced) == 40
    assert store.count() == points and MetadataStore(conn).count_documents() == docs

    jobs = conn.execute("SELECT count(*) AS n FROM ingestion_jobs WHERE status='succeeded'").fetchone()["n"]
    assert jobs == 9
    stat = conn.execute("SELECT DISTINCT ingestion_status FROM knowledge_sources").fetchall()
    assert [r["ingestion_status"] for r in stat] == ["succeeded"]
    row = conn.execute("SELECT * FROM source_documents WHERE document_id='ticket:TKT-115'").fetchone()
    assert row["metadata"]["priority"] == "medium" and row["created_at"].tzinfo is not None
    assert row["indexed_at"] is not None and row["chunk_count"] >= 1


def test_payload_filters_and_dimension_guard(env):
    _, store, qc = env
    hits, _ = qc.scroll("test_chunks", scroll_filter=qm.Filter(must=[
        qm.FieldCondition(key="source_type", match=qm.MatchValue(value="ticket"))]), limit=100)
    assert hits and all(h.payload["source_type"] == "ticket" for h in hits)
    p = hits[0].payload
    for key in ("chunk_id", "document_id", "source_id", "original_record_id", "chunk_index", "text",
                "created_at", "updated_at", "authority_level", "source_reference"):
        assert p[key] is not None
    with pytest.raises(VectorDimensionMismatch):
        store.ensure_collection(DIM + 1)
