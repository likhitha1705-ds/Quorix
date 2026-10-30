"""API route for Step 11: Hybrid Retrieval endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.routes.query import get_query_intelligence_service
from app.core.config import get_settings
from app.intelligence.pipeline import QueryIntelligenceService
from app.retrieval.config import RankingWeights, RetrievalConfig
from app.retrieval.engine import HybridRetrievalEngine
from app.schemas.retrieval import RetrievalRequest, RetrievalResponse

import threading

router = APIRouter(tags=["retrieval"])

_shared_engine: HybridRetrievalEngine | None = None
_init_lock = threading.Lock()


def get_hybrid_retrieval_engine() -> HybridRetrievalEngine:
    """Dependency provider configuring HybridRetrievalEngine with app settings."""
    global _shared_engine
    if _shared_engine is not None:
        return _shared_engine

    with _init_lock:
        if _shared_engine is not None:
            return _shared_engine

        settings = get_settings()
        weights = RankingWeights(
            semantic=settings.retrieval_semantic_weight,
            keyword=settings.retrieval_keyword_weight,
            authority=settings.retrieval_authority_weight,
            freshness=settings.retrieval_freshness_weight,
        )
        config = RetrievalConfig(
            max_sources=settings.retrieval_max_sources,
            max_chunks=settings.retrieval_max_chunks,
            max_context_tokens=settings.retrieval_max_context_tokens,
            max_retrieval_calls=settings.retrieval_max_calls,
            ranking_weights=weights,
            qdrant_collection=settings.qdrant_collection,
        )
        engine = HybridRetrievalEngine(config=config)
        try:
            from app.db.seed_demo import ensure_demo_data_seeded
            ensure_demo_data_seeded(engine.client, engine.embedder, config.qdrant_collection)
        except Exception:
            pass
        _shared_engine = engine
        return _shared_engine


@router.post("/retrieve", response_model=RetrievalResponse)
def retrieve_context(
    request: RetrievalRequest,
    intelligence_svc: QueryIntelligenceService = Depends(get_query_intelligence_service),
    retrieval_engine: HybridRetrievalEngine = Depends(get_hybrid_retrieval_engine),
) -> RetrievalResponse:
    """Execute query analysis, source selection, budget allocation, and hybrid retrieval."""
    query_decision = intelligence_svc.analyze_and_select(request.query)
    retrieval_result = retrieval_engine.retrieve(query_decision)
    return retrieval_result.to_api_response()

