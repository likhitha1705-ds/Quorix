"""Scoring algorithms for intelligent source selection."""
from __future__ import annotations

import math
from datetime import datetime, timezone

from app.intelligence.config import (
    DIRECTNESS_SCORES,
    IntelligenceConfig,
    ScoringWeights,
)
from app.schemas.intelligence import QueryAnalysis, QueryIntent, SourceMetadata


class RelevanceScorer:
    """Heuristic relevance scorer combining topic matching, description overlap, and intent alignment."""

    def score(self, query_analysis: QueryAnalysis, source: SourceMetadata) -> float:
        """Calculate relevance score between query analysis and source metadata in [0.0, 1.0]."""
        # Combine all semantic query tokens
        query_tokens = set(query_analysis.keywords) | {e.lower() for e in query_analysis.entities}
        if not query_tokens:
            return 0.0

        # 1. Topic match: check overlap with supported_topics
        source_topics = {t.lower() for t in source.supported_topics}
        matched_topics = 0
        for token in query_tokens:
            if token in source_topics:
                matched_topics += 1
            else:
                # Substring or common stem match for compound words and inflections
                matched = False
                for topic in source_topics:
                    if token in topic or topic in token:
                        matched = True
                        break
                    if len(token) >= 4 and len(topic) >= 4 and (token[:4] == topic[:4]):
                        matched = True
                        break
                if matched:
                    matched_topics += 1

        topic_score = min(1.0, matched_topics / max(1, min(len(query_tokens), 3)))

        # 2. Description match: check query token occurrences in description and name
        desc_text = f"{source.source_name} {source.description}".lower()
        matched_desc = sum(1 for token in query_tokens if token in desc_text)
        desc_score = min(1.0, matched_desc / max(1, len(query_tokens)))

        # If neither topics nor description matched, the source has no semantic relevance
        if topic_score == 0.0 and desc_score == 0.0:
            return 0.0

        # 3. Preferred source category alignment
        source_type_norm = source.source_type.lower()
        pref_norm = [p.lower() for p in query_analysis.preferred_sources]

        is_preferred = (
            "multi_source" in pref_norm
            or source_type_norm in pref_norm
            or f"{source_type_norm}s" in pref_norm
        )
        pref_score = 1.0 if is_preferred else 0.3

        # Weighted combination of relevance signals
        relevance = (0.45 * topic_score) + (0.35 * desc_score) + (0.20 * pref_score)
        return round(max(0.0, min(1.0, relevance)), 4)


class AuthorityScorer:
    """Authority score normalizer ensuring scores remain in [0.0, 1.0]."""

    def score(self, source: SourceMetadata) -> float:
        """Normalize authority score from source metadata."""
        return round(max(0.0, min(1.0, float(source.authority_score))), 4)


class FreshnessScorer:
    """Freshness scorer using half-life decay, discounting penalty for historical queries."""

    def __init__(self, half_life_days: float = 180.0, historical_discount: float = 0.25) -> None:
        self.half_life_days = half_life_days
        self.historical_discount = historical_discount

    def score(
        self,
        source: SourceMetadata,
        query_analysis: QueryAnalysis,
        now: datetime | None = None,
    ) -> float:
        """Calculate freshness score based on last_updated timestamp and query intent."""
        now = now or datetime.now(timezone.utc)
        last_updated = source.last_updated
        if last_updated.tzinfo is None:
            last_updated = last_updated.replace(tzinfo=timezone.utc)

        delta = (now - last_updated).total_seconds()
        delta_days = max(0.0, delta / 86400.0)

        # Exponential decay: freshness = 2^(-delta_days / half_life)
        raw_freshness = math.exp(-math.log(2) * (delta_days / self.half_life_days))

        # For historical queries, older sources are not penalized as harshly
        if query_analysis.intent == QueryIntent.HISTORICAL_REASON:
            penalty = 1.0 - raw_freshness
            discounted_penalty = penalty * self.historical_discount
            freshness = 1.0 - discounted_penalty
        else:
            freshness = raw_freshness

        return round(max(0.0, min(1.0, freshness)), 4)


class DirectnessScorer:
    """Evaluates how directly a source can answer a given intent based on business rules."""

    def score(self, query_analysis: QueryAnalysis, source: SourceMetadata) -> float:
        """Determine expected directness score for the query intent and source type."""
        intent = query_analysis.intent
        source_type = source.source_type.lower()
        intent_directness = DIRECTNESS_SCORES.get(intent, {})
        return intent_directness.get(source_type, 0.50)


class OverallScorer:
    """Calculates weighted overall score according to configurable criteria weights."""

    def __init__(self, weights: ScoringWeights | None = None) -> None:
        self.weights = weights or ScoringWeights()

    def calculate(
        self,
        relevance: float,
        authority: float,
        freshness: float,
        directness: float,
    ) -> float:
        """Combine individual criterion scores using weighted linear combination."""
        overall = (
            (self.weights.relevance * relevance)
            + (self.weights.authority * authority)
            + (self.weights.freshness * freshness)
            + (self.weights.directness * directness)
        )
        return round(max(0.0, min(1.0, overall)), 4)

