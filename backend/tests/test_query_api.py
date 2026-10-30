"""API integration tests for POST /api/query/analyze."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_api_query_analyze_historical(client: TestClient):
    response = client.post("/api/query/analyze", json={"query": "Why was Redis caching introduced?"})
    assert response.status_code == 200
    data = response.json()

    # Step 13 required top-level fields
    assert data["intent"] == "HISTORICAL_REASON"
    assert "Redis" in data["entities"]
    assert "Caching" in data["entities"]
    assert "redis" in data["keywords"]
    assert "caching" in data["keywords"]
    assert "introduced" in data["keywords"]

    # Verify ranked sources list
    assert len(data["ranked_sources"]) >= 1
    for src in data["ranked_sources"]:
        assert "source_id" in src
        assert "source_name" in src
        assert "source_type" in src
        assert "relevance_score" in src
        assert "authority_score" in src
        assert "freshness_score" in src
        assert "expected_directness_score" in src
        assert "overall_score" in src
        assert "selection_reason" in src
        assert "is_selected" in src

    # Verify selection results
    selected_types = [s["source_type"] for s in data["selected_sources"]]
    assert "conversation" in selected_types

    # Verify selection reasons
    assert len(data["selection_reasons"]) == len(data["ranked_sources"])


def test_api_query_analyze_configuration(client: TestClient):
    response = client.post("/api/query/analyze", json={"query": "How do I configure the Redis port?"})
    assert response.status_code == 200
    data = response.json()

    assert data["intent"] == "CONFIGURATION_LOOKUP"
    assert data["ranked_sources"][0]["source_type"] == "document"
    assert data["ranked_sources"][0]["is_selected"] is True


def test_api_query_analyze_no_matching_source(client: TestClient):
    response = client.post("/api/query/analyze", json={"query": "How to bake a chocolate cake at 350 degrees?"})
    assert response.status_code == 200
    data = response.json()

    # With no matching domain topics, selected_sources must be empty
    assert len(data["selected_sources"]) == 0
    assert len(data["skipped_sources"]) == len(data["ranked_sources"])
    for src in data["skipped_sources"]:
        assert src["is_selected"] is False
        assert "Skipped because:" in src["selection_reason"]


def test_api_query_analyze_validation(client: TestClient):
    # Empty query should fail validation with 422
    response = client.post("/api/query/analyze", json={"query": ""})
    assert response.status_code == 422

