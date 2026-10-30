"""API route for Step 8: Answer Generation & Citation Engine endpoint."""
from __future__ import annotations

import logging
from fastapi import APIRouter, Depends

from app.api.routes.evaluate import get_evidence_intelligence_service
from app.api.routes.query import get_query_intelligence_service
from app.api.routes.retrieve import get_hybrid_retrieval_engine
from app.core.config import get_settings
from app.evaluation.pipeline import EvidenceIntelligenceService
from app.generation.config import GenerationConfig
from app.generation.pipeline import AnswerGenerationService
from app.intelligence.pipeline import QueryIntelligenceService
from app.retrieval.engine import HybridRetrievalEngine
from app.schemas.answer import AnswerRequest, AnswerResponse

log = logging.getLogger(__name__)

router = APIRouter(tags=["answer"])


def get_answer_generation_service() -> AnswerGenerationService:
    """Dependency provider configuring AnswerGenerationService with application settings."""
    settings = get_settings()
    api_key = settings.gemini_api_key.get_secret_value() if settings.gemini_api_key else None
    config = GenerationConfig(
        model_name=settings.gemini_model,
        temperature=settings.generation_temperature,
        max_output_tokens=settings.generation_max_tokens,
        cost_per_million_input_tokens=settings.generation_cost_per_million_input,
        cost_per_million_output_tokens=settings.generation_cost_per_million_output,
        api_key=api_key,
    )
    return AnswerGenerationService(config=config)


@router.post("/answer", response_model=AnswerResponse)
def generate_grounded_answer(
    request: AnswerRequest,
    intelligence_svc: QueryIntelligenceService = Depends(get_query_intelligence_service),
    retrieval_engine: HybridRetrievalEngine = Depends(get_hybrid_retrieval_engine),
    evaluation_svc: EvidenceIntelligenceService = Depends(get_evidence_intelligence_service),
    generation_svc: AnswerGenerationService = Depends(get_answer_generation_service),
) -> AnswerResponse:
    """Execute end-to-end grounded RAG: query analysis, source selection, retrieval, evidence evaluation, and answer generation."""
    log.info("=" * 80)
    log.info("[RAG STAGE 1] Incoming query: %r", request.query)

    # 1. Query Analysis & Source Selection (Phase 3)
    query_decision = intelligence_svc.analyze_and_select(request.query)
    selected_source_ids = [s.source_id for s in query_decision.selected_sources]
    log.info("[RAG STAGE 2] Selected sources (%d): %s (Skipped: %s)",
             len(selected_source_ids), selected_source_ids, [s.source_id for s in query_decision.skipped_sources])

    # 2. Retrieval Budget & Hybrid Retrieval (Phase 4)
    retrieval_result = retrieval_engine.retrieve(query_decision)
    chunk_summaries = [
        f"[{c.chunk_id}] src={c.source_id} sim={c.similarity_score:.4f} kw={c.keyword_score:.4f} final={c.final_score:.4f}"
        for c in retrieval_result.retrieved_chunks
    ]
    log.info("[RAG STAGE 3] Retrieved chunks & similarity scores (%d chunks, %d tokens):\n  %s",
             len(retrieval_result.retrieved_chunks),
             retrieval_result.retrieval_metrics.estimated_tokens,
             "\n  ".join(chunk_summaries) if chunk_summaries else "None")

    # 3. Evidence Intelligence & Sufficiency Evaluation (Phase 5)
    evaluation_result = evaluation_svc.evaluate(retrieval_result)
    log.info("[RAG STAGE 4] Evidence decision: %s | Confidence: %.4f | Strongest chunks: %s",
             evaluation_result.evidence_decision.value,
             evaluation_result.confidence_score,
             [c.chunk_id for c in evaluation_result.evidence_summary.strongest_evidence])

    # 4. Grounded Answer Generation & Citation Construction (Phase 6)
    answer_result = generation_svc.generate_answer(evaluation_result)
    log.info("[RAG STAGE 5] Gemini / Generation response:\n  Answer: %s\n  Citations: %s\n  Decision: %s",
             answer_result.answer,
             [c.chunk_id for c in answer_result.citations],
             answer_result.evidence_decision.value)
    log.info("=" * 80)

    return answer_result.to_api_response()
