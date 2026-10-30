"""API route for Step 12: Evidence Evaluation endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.routes.query import get_query_intelligence_service
from app.api.routes.retrieve import get_hybrid_retrieval_engine
from app.core.config import get_settings
from app.evaluation.config import EvaluationConfig, EvidenceScoringWeights
from app.evaluation.pipeline import EvidenceIntelligenceService
from app.intelligence.pipeline import QueryIntelligenceService
from app.retrieval.engine import HybridRetrievalEngine
from app.schemas.evaluation import EvidenceEvaluationRequest, EvidenceEvaluationResponse

router = APIRouter(tags=["evaluation"])


def get_evidence_intelligence_service() -> EvidenceIntelligenceService:
    """Dependency provider configuring EvidenceIntelligenceService with application settings."""
    settings = get_settings()
    weights = EvidenceScoringWeights(
        relevance=settings.evaluation_relevance_weight,
        authority=settings.evaluation_authority_weight,
        directness=settings.evaluation_directness_weight,
        freshness=settings.evaluation_freshness_weight,
    )
    config = EvaluationConfig(
        weights=weights,
        sufficient_threshold=settings.evaluation_sufficient_threshold,
        unsupported_threshold=settings.evaluation_unsupported_threshold,
    )
    return EvidenceIntelligenceService(config=config)


@router.post("/evaluate", response_model=EvidenceEvaluationResponse)
def evaluate_evidence(
    request: EvidenceEvaluationRequest,
    intelligence_svc: QueryIntelligenceService = Depends(get_query_intelligence_service),
    retrieval_engine: HybridRetrievalEngine = Depends(get_hybrid_retrieval_engine),
    evaluation_svc: EvidenceIntelligenceService = Depends(get_evidence_intelligence_service),
) -> EvidenceEvaluationResponse:
    """Execute end-to-end intelligence: query analysis, source selection, hybrid retrieval, and evidence sufficiency evaluation."""
    # 1. Query Analysis & Source Selection (Phase 3)
    query_decision = intelligence_svc.analyze_and_select(request.query)

    # 2. Retrieval Budget & Hybrid Retrieval (Phase 4)
    retrieval_result = retrieval_engine.retrieve(query_decision)

    # 3. Evidence Intelligence & Sufficiency Evaluation (Phase 5)
    evaluation_result = evaluation_svc.evaluate(retrieval_result)

    return evaluation_result.to_api_response()

