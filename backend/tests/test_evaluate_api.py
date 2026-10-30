"""API integration tests for POST /api/evaluate."""
from __future__ import annotations

from datetime import datetime, timezone

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
    now = datetime.now(timezone.utc)
    return [
        RetrievedChunk(
            chunk_id="chunk_doc_1",
            source_id="src_documents",
            source_type="document",
            source_name="Architecture Docs",
            content="Official architecture decision: Redis caching was introduced because database read latency exceeded acceptable SLA limits.",
            similarity_score=0.92,
            keyword_score=0.85,
            final_score=0.92,
            timestamp=now,
            metadata={"authority_level": "high", "title": "Architecture Overview"},
        ),
        RetrievedChunk(
            chunk_id="chunk_conv_1",
            source_id="src_conversations",
            source_type="conversation",
            source_name="Engineering Discussions",
            content="Engineering team discussion: we decided to introduce Redis because Postgres CPU was spiking on session reads.",
            similarity_score=0.88,
            keyword_score=0.80,
            final_score=0.88,
            timestamp=now,
            metadata={"authority_level": "medium", "decision": True},
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


def test_api_evaluate_sufficient(client: TestClient):
    response = client.post("/api/evaluate", json={"query": "Why was Redis caching introduced?"})
    assert response.status_code == 200
    data = response.json()

    # Step 12 Schema Verification
    assert "evaluated_chunks" in data
    assert "evidence_summary" in data
    assert "conflicts" in data
    assert "confidence" in data
    assert "decision" in data
    assert "needs_more_retrieval" in data
    assert "evaluation_explanation" in data
    assert "retrieval_metrics" in data

    # Verifications
    assert data["decision"] == "SUFFICIENT"
    assert data["needs_more_retrieval"] is False
    assert data["confidence"] >= 0.70
    assert len(data["evaluated_chunks"]) >= 1

    first_chunk = data["evaluated_chunks"][0]
    assert "chunk_id" in first_chunk
    assert "source" in first_chunk
    assert "score" in first_chunk
    assert "relevance_score" in first_chunk
    assert "authority_score" in first_chunk
    assert "freshness_score" in first_chunk
    assert "directness_score" in first_chunk
    assert "confidence_score" in first_chunk
    assert "explanation" in first_chunk

    summary = data["evidence_summary"]
    assert summary["total_evaluated_chunks"] == len(data["evaluated_chunks"])
    assert summary["average_confidence"] > 0.0
    assert summary["highest_confidence"] >= summary["average_confidence"]


def test_api_evaluate_conflicting():
    now = datetime.now(timezone.utc)
    conflicting_chunks = [
        RetrievedChunk(
            chunk_id="chunk_doc_1",
            source_id="src_documents",
            source_type="document",
            source_name="Architecture Docs",
            content="redis ttl = 600 seconds by default for session tokens.",
            similarity_score=0.90,
            keyword_score=0.85,
            final_score=0.90,
            timestamp=now,
            metadata={"authority_level": "high"},
        ),
        RetrievedChunk(
            chunk_id="chunk_doc_2",
            source_id="src_documents",
            source_type="document",
            source_name="Deployment Guide",
            content="redis ttl = 300 seconds is configured in production.",
            similarity_score=0.88,
            keyword_score=0.80,
            final_score=0.88,
            timestamp=now,
            metadata={"authority_level": "high"},
        ),
    ]

    registry = RetrievalAdapterRegistry([
        InMemoryAdapter("document", conflicting_chunks),
        InMemoryAdapter("conversation", conflicting_chunks),
        InMemoryAdapter("ticket", []),
    ])
    mock_engine = HybridRetrievalEngine(
        config=RetrievalConfig(max_chunks=5),
        embedder=DummyEmbedder(),
        semantic_engine=SemanticRetrievalEngine(embedder=DummyEmbedder(), adapter_registry=registry),
    )

    app.dependency_overrides[get_hybrid_retrieval_engine] = lambda: mock_engine
    c = TestClient(app)
    try:
        response = c.post("/api/evaluate", json={"query": "What is the Redis cache TTL?"})
        assert response.status_code == 200
        data = response.json()

        assert data["decision"] == "CONFLICTING"
        assert len(data["conflicts"]) >= 1
        assert "ttl" in data["conflicts"][0]["conflicting_fields"]
        assert data["needs_more_retrieval"] is True
    finally:
        app.dependency_overrides.clear()


def test_api_evaluate_unsupported(client: TestClient):
    response = client.post("/api/evaluate", json={"query": "How to bake a chocolate cake at 350 degrees?"})
    assert response.status_code == 200
    data = response.json()

    assert data["decision"] == "UNSUPPORTED"
    assert data["confidence"] == 0.0
    assert len(data["evaluated_chunks"]) == 0
    assert "unsupported" in data["evaluation_explanation"].lower()


def test_api_evaluate_validation_error(client: TestClient):
    response = client.post("/api/evaluate", json={"query": ""})
    assert response.status_code == 422
