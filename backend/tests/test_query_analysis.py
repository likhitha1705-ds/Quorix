"""Unit tests for Step 1: Query Analysis Engine."""
from __future__ import annotations

import pytest

from app.intelligence.query_analysis import QueryAnalysisEngine
from app.schemas.intelligence import QueryIntent


@pytest.fixture
def engine() -> QueryAnalysisEngine:
    return QueryAnalysisEngine()


def test_intent_detection_historical_reason(engine: QueryAnalysisEngine):
    res = engine.analyze("Why was Redis caching introduced?")
    assert res.intent == QueryIntent.HISTORICAL_REASON
    assert res.expected_information_type == "decision_history"
    assert "conversations" in res.preferred_sources


def test_intent_detection_configuration_lookup(engine: QueryAnalysisEngine):
    res = engine.analyze("How do I configure the Redis connection pool and port?")
    assert res.intent == QueryIntent.CONFIGURATION_LOOKUP
    assert res.expected_information_type == "configuration_reference"
    assert "documents" in res.preferred_sources


def test_intent_detection_bug_investigation(engine: QueryAnalysisEngine):
    res = engine.analyze("Why is the ingestion pipeline throwing ConnectionError timeout bug?")
    assert res.intent == QueryIntent.BUG_INVESTIGATION
    assert res.expected_information_type == "incident_troubleshooting"
    assert "tickets" in res.preferred_sources or "conversations" in res.preferred_sources


def test_intent_detection_feature_information(engine: QueryAnalysisEngine):
    res = engine.analyze("Does Quorix support PDF sidecar metadata files?")
    assert res.intent == QueryIntent.FEATURE_INFORMATION
    assert res.expected_information_type == "feature_specification"


def test_intent_detection_implementation_details(engine: QueryAnalysisEngine):
    res = engine.analyze("How is the ChunkingService implemented under the hood?")
    assert res.intent == QueryIntent.IMPLEMENTATION_DETAILS
    assert res.expected_information_type == "code_implementation"


def test_intent_detection_technical_explanation(engine: QueryAnalysisEngine):
    res = engine.analyze("Explain the architecture of the vector search pipeline")
    assert res.intent == QueryIntent.TECHNICAL_EXPLANATION
    assert res.expected_information_type == "architectural_explanation"


def test_intent_detection_general_information(engine: QueryAnalysisEngine):
    res = engine.analyze("System overview")
    assert res.intent == QueryIntent.GENERAL_INFORMATION


def test_entity_extraction_redis_caching(engine: QueryAnalysisEngine):
    res = engine.analyze("Why was Redis caching introduced?")
    assert "Redis" in res.entities
    assert "Caching" in res.entities
    # Common question words like "Why" should not be extracted as entities
    assert "Why" not in res.entities


def test_entity_extraction_pascal_and_technical(engine: QueryAnalysisEngine):
    res = engine.analyze("How does ChunkingService interact with PostgreSQL and Qdrant?")
    assert "ChunkingService" in res.entities
    assert "PostgreSQL" in res.entities
    assert "Qdrant" in res.entities


def test_keyword_extraction_filters_stop_words(engine: QueryAnalysisEngine):
    keywords = engine.extract_keywords("Why was Redis caching introduced?")
    assert "redis" in keywords
    assert "caching" in keywords
    assert "introduced" in keywords
    assert "why" not in keywords
    assert "was" not in keywords


def test_multi_source_hint_detection(engine: QueryAnalysisEngine):
    # Query with multiple hints across docs, discussions, and tickets
    res = engine.analyze("Review the architecture doc, team discussion, and bug ticket for Redis")
    assert res.preferred_sources == ["multi_source"]

