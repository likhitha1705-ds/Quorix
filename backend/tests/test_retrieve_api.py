"""API integration tests for POST /api/retrieve."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.routes.retrieve import get_hybrid_retrieval_engine
from app.main import app
from app.retrieval.adapters import BaseRetrievalAdapter, RetrievalAdapterRegistry
from app.retrieval.config import RetrievalConfig
from app.retrieval.engine import HybridRetrievalEngine
from app.retrieval.semantic import SemanticRetrievalEngine
from app.schemas.retrieval import RetrievedChunk


class InMemoryAdapter(BaseRetrievalAdapter):
    def __init__(self, source_type: str, chunks: list[RetrievedChunk]) -> None:
        self.source_type = source_type
        self.chunks = chunks

    def retrieve(
        self,
        query: str,
        query_vector: list[float] | None,
        source_id: str,
        limit: int,
        source_name: str | None = None,
    ) -> list[RetrievedChunk]:
        return [c for c in self.chunks if c.source_id == source_id][:limit]


class DummyEmbedder:
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * 8 for _ in texts]

    def embed_query(self, query: str) -> list[float]:
        return [0.1] * 8


@pytest.fixture
def test_chunks() -> list[RetrievedChunk]:
    return [
        RetrievedChunk(
            chunk_id="chunk_doc_1",
            source_id="src_documents",
            source_type="document",
            source_name="Technical Documents",
            content="Redis caching architecture was introduced to handle high-throughput session reads.",
            similarity_score=0.85,
            keyword_score=0.7,
            final_score=0.85,
            metadata={"source_reference": "docs/arch.md", "title": "Architecture Overview"},
        ),
        RetrievedChunk(
            chunk_id="chunk_conv_1",
            source_id="src_conversations",
            source_type="conversation",
            source_name="Engineering Conversations",
            content="Team discussion: why we chose Redis for cache instead of Memcached.",
            similarity_score=0.90,
            keyword_score=0.8,
            final_score=0.90,
            metadata={"source_reference": "convs/redis_discussion.json", "title": "Redis Decision"},
        ),
    ]


@pytest.fixture
def client(test_chunks: list[RetrievedChunk]) -> TestClient:
    registry = RetrievalAdapterRegistry([
        InMemoryAdapter("document", test_chunks),
        InMemoryAdapter("conversation", test_chunks),
        InMemoryAdapter("ticket", []),
    ])
    mock_engine = HybridRetrievalEngine(
        config=RetrievalConfig(max_chunks=5),
        embedder=DummyEmbedder(),
        semantic_engine=SemanticRetrievalEngine(embedder=DummyEmbedder(), adapter_registry=registry),
    )

    app.dependency_overrides[get_hybrid_retrieval_engine] = lambda: mock_engine
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_api_retrieve_success(client: TestClient):
    response = client.post("/api/retrieve", json={"query": "Why was Redis caching introduced?"})
    assert response.status_code == 200
    data = response.json()

    # Step 12 required top-level structure
    assert "query_analysis" in data
    assert "selected_sources" in data
    assert "retrieval_budget" in data
    assert "retrieved_chunks" in data
    assert "retrieval_metrics" in data

    # Verify query analysis fields
    assert data["query_analysis"]["intent"] == "HISTORICAL_REASON"
    assert "Redis" in data["query_analysis"]["entities"]

    # Verify retrieval budget
    assert data["retrieval_budget"]["max_sources"] == 3
    assert data["retrieval_budget"]["max_chunks"] == 5
    assert data["retrieval_budget"]["max_context_tokens"] == 4000

    # Verify retrieved chunks structure matching Step 12
    assert len(data["retrieved_chunks"]) >= 1
    for chunk in data["retrieved_chunks"]:
        # Required in Step 12: source, score, metadata, content
        assert "source" in chunk
        assert "score" in chunk
        assert "metadata" in chunk
        assert "content" in chunk
        # Also contains normalized fields
        assert "chunk_id" in chunk
        assert "source_id" in chunk
        assert "source_type" in chunk

    # Verify retrieval metrics
    metrics = data["retrieval_metrics"]
    assert metrics["retrieval_calls"] >= 1
    assert metrics["retrieved_chunks"] == len(data["retrieved_chunks"])
    assert "retrieval_budget_consumed" in metrics


def test_api_retrieve_no_matching_source(client: TestClient):
    response = client.post("/api/retrieve", json={"query": "How to bake a chocolate cake at 350 degrees?"})
    assert response.status_code == 200
    data = response.json()

    # Unrelated query -> no sources selected in Phase 3 -> 0 chunks retrieved
    assert len(data["selected_sources"]) == 0
    assert len(data["retrieved_chunks"]) == 0
    assert data["retrieval_metrics"]["retrieved_chunks"] == 0
    assert data["retrieval_metrics"]["retrieval_calls"] == 0


def test_api_retrieve_validation_error(client: TestClient):
    response = client.post("/api/retrieve", json={"query": ""})
    assert response.status_code == 422

