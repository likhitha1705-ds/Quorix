"""Orchestration service for Phase 3: Query Analysis & Intelligent Source Selection."""
from __future__ import annotations

import logging
import time
from typing import Any

from app.intelligence.config import IntelligenceConfig
from app.intelligence.query_analysis import QueryAnalysisEngine
from app.intelligence.source_registry import SourceRegistryService
from app.intelligence.source_selection import SourceSelectionEngine
from app.schemas.intelligence import QueryDecision, SourceMetadata

log = logging.getLogger(__name__)


class QueryIntelligenceService:
    """Orchestrates query analysis, source discovery, and intelligent source selection."""

    def __init__(
        self,
        analysis_engine: QueryAnalysisEngine | None = None,
        source_registry: SourceRegistryService | None = None,
        selection_engine: SourceSelectionEngine | None = None,
        config: IntelligenceConfig | None = None,
    ) -> None:
        self.config = config or IntelligenceConfig()
        self.analysis_engine = analysis_engine or QueryAnalysisEngine()
        self.source_registry = source_registry or SourceRegistryService()
        self.selection_engine = selection_engine or SourceSelectionEngine(config=self.config)

    def analyze_and_select(
        self,
        query: str,
        sources_override: list[SourceMetadata] | None = None,
    ) -> QueryDecision:
        """Execute the Phase 3 intelligence pipeline without retrieving any documents."""
        start_time = time.perf_counter()

        # Step 1: Query Analysis
        query_analysis = self.analysis_engine.analyze(query)

        # Step 2: Source Registry
        sources = sources_override if sources_override is not None else self.source_registry.get_available_sources()

        # Step 3: Source Selection & Ranking
        ranked_sources, selected_sources, skipped_sources, selection_reasons = (
            self.selection_engine.select_sources(query_analysis, sources)
        )

        execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Step 14: Structured Logging
        log.info(
            "Query analysis executed in %.2fms | Query: %r | Intent: %s | Entities: %s | "
            "Ranked: %s | Selected: %s",
            execution_time_ms,
            query,
            query_analysis.intent.value,
            query_analysis.entities,
            [f"{s.source_id}({s.overall_score:.2f})" for s in ranked_sources],
            [s.source_id for s in selected_sources],
        )

        # Reusable QueryDecision object for Phase 4 handoff
        return QueryDecision(
            query_analysis=query_analysis,
            ranked_sources=ranked_sources,
            selected_sources=selected_sources,
            skipped_sources=skipped_sources,
            selection_reasons=selection_reasons,
            retrieval_constraints={
                "max_chunks_per_source": 5,
                "confidence_threshold": self.config.confidence_threshold,
                "preferred_categories": query_analysis.preferred_sources,
            },
            metadata={
                "execution_time_ms": execution_time_ms,
                "total_available_sources": len(sources),
                "selected_source_count": len(selected_sources),
            },
        )

