"""Source Selection Engine: scores, ranks, and filters candidate knowledge sources."""
from __future__ import annotations

import logging
from typing import Any

from app.intelligence.config import IntelligenceConfig
from app.intelligence.scoring import (
    AuthorityScorer,
    DirectnessScorer,
    FreshnessScorer,
    OverallScorer,
    RelevanceScorer,
)
from app.schemas.intelligence import (
    QueryAnalysis,
    QueryIntent,
    RankedSource,
    SourceMetadata,
)

log = logging.getLogger(__name__)


class SourceSelectionEngine:
    """Evaluates candidate knowledge sources against a query analysis to rank and select them."""

    def __init__(self, config: IntelligenceConfig | None = None) -> None:
        self.config = config or IntelligenceConfig()
        self.relevance_scorer = RelevanceScorer()
        self.authority_scorer = AuthorityScorer()
        self.freshness_scorer = FreshnessScorer(
            half_life_days=self.config.freshness_half_life_days,
            historical_discount=self.config.historical_penalty_discount,
        )
        self.directness_scorer = DirectnessScorer()
        self.overall_scorer = OverallScorer(weights=self.config.weights)

    def select_sources(
        self,
        query_analysis: QueryAnalysis,
        available_sources: list[SourceMetadata],
    ) -> tuple[list[RankedSource], list[RankedSource], list[RankedSource], list[str]]:
        """Score, rank, and select sources based on configured threshold and selection limits."""
        scored_candidates: list[dict[str, Any]] = []

        for src in available_sources:
            rel = self.relevance_scorer.score(query_analysis, src)
            auth = self.authority_scorer.score(src)
            fresh = self.freshness_scorer.score(src, query_analysis)
            direct = self.directness_scorer.score(query_analysis, src)
            overall = self.overall_scorer.calculate(rel, auth, fresh, direct)

            scored_candidates.append(
                {
                    "source": src,
                    "relevance": rel,
                    "authority": auth,
                    "freshness": fresh,
                    "directness": direct,
                    "overall": overall,
                }
            )

        # Sort sources in descending order of overall score
        scored_candidates.sort(key=lambda item: item["overall"], reverse=True)

        ranked_sources: list[RankedSource] = []
        selected_sources: list[RankedSource] = []
        skipped_sources: list[RankedSource] = []
        selection_reasons: list[str] = []

        for idx, item in enumerate(scored_candidates, start=1):
            src: SourceMetadata = item["source"]
            overall = item["overall"]
            rel = item["relevance"]
            auth = item["authority"]
            fresh = item["freshness"]
            direct = item["directness"]

            is_selected = False
            reason: str

            if overall < self.config.confidence_threshold or rel < self.config.min_relevance_threshold:
                if rel < self.config.min_relevance_threshold:
                    reason = (
                        f"Skipped because: Low expected relevance for this query "
                        f"(relevance: {rel:.2f}, overall score: {overall:.2f})."
                    )
                else:
                    reason = (
                        f"Skipped because: Overall score ({overall:.2f}) is below confidence threshold "
                        f"({self.config.confidence_threshold:.2f})."
                    )
            elif len(selected_sources) >= self.config.max_selected_sources:
                reason = (
                    f"Skipped because: Exceeded maximum selected sources limit ({self.config.max_selected_sources}) "
                    f"(ranked #{idx} with overall score {overall:.2f})."
                )
            else:
                is_selected = True
                matched_summary = self._generate_selection_summary(query_analysis, src, direct, rel)
                reason = (
                    f"Selected because: {matched_summary} "
                    f"(overall score: {overall:.2f} exceeds threshold {self.config.confidence_threshold:.2f})."
                )

            ranked = RankedSource(
                source_id=src.source_id,
                source_name=src.source_name,
                source_type=src.source_type,
                relevance_score=rel,
                authority_score=auth,
                freshness_score=fresh,
                expected_directness_score=direct,
                overall_score=overall,
                selection_reason=reason,
                is_selected=is_selected,
            )

            ranked_sources.append(ranked)
            selection_reasons.append(f"{src.source_name}: {reason}")

            if is_selected:
                selected_sources.append(ranked)
            else:
                skipped_sources.append(ranked)

        return ranked_sources, selected_sources, skipped_sources, selection_reasons

    @staticmethod
    def _generate_selection_summary(
        query_analysis: QueryAnalysis,
        source: SourceMetadata,
        directness: float,
        relevance: float,
    ) -> str:
        """Create informative reason explaining why the source was selected."""
        intent = query_analysis.intent
        stype = source.source_type.lower()
        entities = query_analysis.entities

        entity_phrase = f" relevant to {', '.join(entities[:2])}" if entities else ""

        if intent == QueryIntent.HISTORICAL_REASON:
            if stype == "conversation":
                return f"Contains historical engineering discussions and design rationale{entity_phrase}."
            if stype == "document":
                return f"Contains architectural design documents and decision records{entity_phrase}."
            return f"Contains historical context regarding {', '.join(entities[:2]) if entities else 'the issue'}."

        if intent == QueryIntent.CONFIGURATION_LOOKUP:
            if stype == "document":
                return f"Contains authoritative configuration and setup documentation{entity_phrase}."
            return f"Contains configuration references and setup discussions{entity_phrase}."

        if intent == QueryIntent.BUG_INVESTIGATION:
            if stype == "ticket":
                return f"Contains issue tracking, bug reports, and resolution history{entity_phrase}."
            if stype == "conversation":
                return f"Contains developer debugging threads and incident discussions{entity_phrase}."
            return f"Contains technical documentation relevant to troubleshooting."

        if intent == QueryIntent.FEATURE_INFORMATION:
            if stype == "document":
                return f"Contains feature specifications, architecture, and documentation{entity_phrase}."
            if stype == "ticket":
                return f"Contains feature request status and implementation tracking{entity_phrase}."
            return f"Contains discussions regarding feature capabilities."

        if intent == QueryIntent.IMPLEMENTATION_DETAILS:
            if stype == "document":
                return f"Contains technical architecture and component implementation details{entity_phrase}."
            return f"Contains implementation discussions and code context."

        if intent == QueryIntent.TECHNICAL_EXPLANATION:
            if stype == "document":
                return f"Contains comprehensive architectural documentation{entity_phrase}."
            return f"Contains engineering explanations and technical context."

        return f"High expected relevance and directness for answering this query{entity_phrase}."
