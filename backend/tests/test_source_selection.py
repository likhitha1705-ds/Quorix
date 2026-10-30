"""Unit tests for Steps 3-12: Source Selection Engine, Scoring, Ranking, and Rules."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.intelligence.config import IntelligenceConfig, ScoringWeights
from app.intelligence.query_analysis import QueryAnalysisEngine
from app.intelligence.scoring import (
    AuthorityScorer,
    DirectnessScorer,
    FreshnessScorer,
    OverallScorer,
    RelevanceScorer,
)
from app.intelligence.source_registry import SourceRegistryService
from app.intelligence.source_selection import SourceSelectionEngine
from app.schemas.intelligence import QueryAnalysis, QueryIntent, SourceMetadata


@pytest.fixture
def default_sources() -> list[SourceMetadata]:
    return SourceRegistryService.get_default_sources()


@pytest.fixture
def analysis_engine() -> QueryAnalysisEngine:
    return QueryAnalysisEngine()


@pytest.fixture
def selection_engine() -> SourceSelectionEngine:
    return SourceSelectionEngine()


def test_scoring_weights_validation():
    # Valid weights that sum to 1.0
    w = ScoringWeights(relevance=0.35, authority=0.25, freshness=0.20, directness=0.20)
    assert w.relevance == 0.35

    # Invalid weights that do not sum to 1.0
    with pytest.raises(ValueError):
        ScoringWeights(relevance=0.5, authority=0.5, freshness=0.5, directness=0.5)


def test_overall_scorer_formula():
    scorer = OverallScorer(ScoringWeights(relevance=0.35, authority=0.25, freshness=0.20, directness=0.20))
    score = scorer.calculate(relevance=1.0, authority=0.8, freshness=0.5, directness=0.9)
    # 0.35*1.0 + 0.25*0.8 + 0.20*0.5 + 0.20*0.9 = 0.35 + 0.20 + 0.10 + 0.18 = 0.83
    assert abs(score - 0.83) < 1e-4


def test_freshness_scorer_historical_discount():
    fresh_scorer = FreshnessScorer(half_life_days=180.0, historical_discount=0.25)
    now = datetime.now(timezone.utc)
    old_time = now - timedelta(days=360)

    source = SourceMetadata(
        source_id="src_conv",
        source_name="Old Conversations",
        source_type="conversation",
        description="Engineering conversations",
        authority_score=0.5,
        last_updated=old_time,
        supported_topics=["history"],
    )

    norm_analysis = QueryAnalysis(
        query="Current bug in redis",
        intent=QueryIntent.BUG_INVESTIGATION,
        keywords=["bug", "redis"],
        entities=["Redis"],
        expected_information_type="incident_troubleshooting",
        preferred_sources=["tickets"],
    )
    hist_analysis = QueryAnalysis(
        query="Why was Redis introduced?",
        intent=QueryIntent.HISTORICAL_REASON,
        keywords=["redis", "introduced"],
        entities=["Redis"],
        expected_information_type="decision_history",
        preferred_sources=["conversations"],
    )

    norm_freshness = fresh_scorer.score(source, norm_analysis, now=now)
    hist_freshness = fresh_scorer.score(source, hist_analysis, now=now)

    # Historical query should reduce freshness penalty, resulting in a higher freshness score
    assert hist_freshness > norm_freshness


def test_directness_scoring_business_logic():
    direct_scorer = DirectnessScorer()

    doc_source = SourceMetadata(
        source_id="src_doc",
        source_name="Docs",
        source_type="document",
        description="Docs",
        authority_score=0.85,
        last_updated=datetime.now(timezone.utc),
    )
    conv_source = SourceMetadata(
        source_id="src_conv",
        source_name="Conversations",
        source_type="conversation",
        description="Discussions",
        authority_score=0.50,
        last_updated=datetime.now(timezone.utc),
    )

    # For Configuration Lookup: Document > Conversation
    config_analysis = QueryAnalysis(
        query="configure redis",
        intent=QueryIntent.CONFIGURATION_LOOKUP,
        keywords=["configure", "redis"],
        entities=["Redis"],
        expected_information_type="configuration_reference",
        preferred_sources=["documents"],
    )
    assert direct_scorer.score(config_analysis, doc_source) > direct_scorer.score(config_analysis, conv_source)

    # For Historical Reason: Conversation > Document
    hist_analysis = QueryAnalysis(
        query="why redis",
        intent=QueryIntent.HISTORICAL_REASON,
        keywords=["why", "redis"],
        entities=["Redis"],
        expected_information_type="decision_history",
        preferred_sources=["conversations"],
    )
    assert direct_scorer.score(hist_analysis, conv_source) > direct_scorer.score(hist_analysis, doc_source)


def test_scenario_configuration_lookup(
    analysis_engine: QueryAnalysisEngine,
    selection_engine: SourceSelectionEngine,
    default_sources: list[SourceMetadata],
):
    analysis = analysis_engine.analyze("How do I configure the Redis port and connection pool?")
    assert analysis.intent == QueryIntent.CONFIGURATION_LOOKUP

    ranked, selected, skipped, reasons = selection_engine.select_sources(analysis, default_sources)

    # Documents should rank #1 and be selected
    assert len(ranked) == 3
    assert ranked[0].source_type == "document"
    assert ranked[0].is_selected is True
    assert "Selected because: Contains authoritative configuration" in ranked[0].selection_reason


def test_scenario_historical_reasoning(
    analysis_engine: QueryAnalysisEngine,
    selection_engine: SourceSelectionEngine,
    default_sources: list[SourceMetadata],
):
    analysis = analysis_engine.analyze("Why was Redis caching introduced?")
    assert analysis.intent == QueryIntent.HISTORICAL_REASON

    ranked, selected, skipped, reasons = selection_engine.select_sources(analysis, default_sources)

    # Conversations should be top-ranked or selected
    selected_types = [s.source_type for s in selected]
    assert "conversation" in selected_types
    # Ticket should be skipped (lower directness/relevance)
    conv_source = next(s for s in ranked if s.source_type == "conversation")
    assert conv_source.is_selected is True
    assert "Selected because:" in conv_source.selection_reason
    assert "Contains historical engineering discussions" in conv_source.selection_reason


def test_scenario_bug_investigation(
    analysis_engine: QueryAnalysisEngine,
    selection_engine: SourceSelectionEngine,
    default_sources: list[SourceMetadata],
):
    analysis = analysis_engine.analyze("Why is the ingestion pipeline throwing ConnectionError timeout bug?")
    assert analysis.intent == QueryIntent.BUG_INVESTIGATION

    ranked, selected, skipped, reasons = selection_engine.select_sources(analysis, default_sources)

    # Ticket should be ranked #1
    assert ranked[0].source_type == "ticket"
    assert ranked[0].is_selected is True
    assert "issue tracking" in ranked[0].selection_reason or "bug reports" in ranked[0].selection_reason


def test_scenario_feature_request(
    analysis_engine: QueryAnalysisEngine,
    selection_engine: SourceSelectionEngine,
    default_sources: list[SourceMetadata],
):
    analysis = analysis_engine.analyze("What is the roadmap and status for PDF sidecar metadata feature?")
    assert analysis.intent == QueryIntent.FEATURE_INFORMATION

    ranked, selected, skipped, reasons = selection_engine.select_sources(analysis, default_sources)

    selected_types = [s.source_type for s in selected]
    assert "document" in selected_types or "ticket" in selected_types


def test_scenario_multi_source_query(
    analysis_engine: QueryAnalysisEngine,
    selection_engine: SourceSelectionEngine,
    default_sources: list[SourceMetadata],
):
    analysis = analysis_engine.analyze("Check the technical documents, team conversations, and bug tickets for redis")
    assert analysis.preferred_sources == ["multi_source"]

    ranked, selected, skipped, reasons = selection_engine.select_sources(analysis, default_sources)
    assert len(selected) >= 2


def test_scenario_no_matching_source(
    analysis_engine: QueryAnalysisEngine,
    default_sources: list[SourceMetadata],
):
    # Completely off-topic query with zero matching topics or keywords
    analysis = analysis_engine.analyze("How to bake a chocolate cake at 350 degrees?")

    # With confidence threshold of 0.50
    custom_config = IntelligenceConfig(confidence_threshold=0.50)
    engine = SourceSelectionEngine(config=custom_config)

    ranked, selected, skipped, reasons = engine.select_sources(analysis, default_sources)

    # All sources should have low relevance (0.0) and be skipped
    assert len(selected) == 0
    assert len(skipped) == 3
    for s in ranked:
        assert s.is_selected is False
        assert "Skipped because:" in s.selection_reason


def test_sorting_and_ranking_order(
    analysis_engine: QueryAnalysisEngine,
    selection_engine: SourceSelectionEngine,
    default_sources: list[SourceMetadata],
):
    analysis = analysis_engine.analyze("Redis caching architecture")
    ranked, selected, skipped, reasons = selection_engine.select_sources(analysis, default_sources)

    # Verify descending sort order
    for i in range(len(ranked) - 1):
        assert ranked[i].overall_score >= ranked[i + 1].overall_score


def test_max_selected_sources_cutoff(
    analysis_engine: QueryAnalysisEngine,
    default_sources: list[SourceMetadata],
):
    analysis = analysis_engine.analyze("Redis caching architecture")

    # Limit max selected sources to 1 with low threshold
    config = IntelligenceConfig(confidence_threshold=0.20, max_selected_sources=1)
    engine = SourceSelectionEngine(config=config)

    ranked, selected, skipped, reasons = engine.select_sources(analysis, default_sources)

    assert len(selected) == 1
    assert len(skipped) == 2
    # The 2nd ranked source was skipped due to max source limit
    assert "Exceeded maximum selected sources limit" in ranked[1].selection_reason

