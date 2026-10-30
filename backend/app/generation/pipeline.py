"""Answer Generation Service orchestrating prompt construction, LLM generation, citation extraction, and execution metric tracking."""
from __future__ import annotations

import logging
import time
from typing import Any

from app.generation.citations import CitationEngine
from app.generation.config import GenerationConfig
from app.generation.llm import GeminiService
from app.generation.prompts import PromptBuilder
from app.schemas.answer import AnswerExecutionMetrics, AnswerResult
from app.schemas.evaluation import EvidenceDecision, EvidenceEvaluationResult

log = logging.getLogger(__name__)


class AnswerGenerationService:
    """Core service for Phase 6: Answer Generation & Citation Engine."""

    def __init__(
        self,
        config: GenerationConfig | None = None,
        llm_service: GeminiService | None = None,
        citation_engine: CitationEngine | None = None,
        prompt_builder: PromptBuilder | None = None,
    ) -> None:
        self.config = config or GenerationConfig()
        self.llm_service = llm_service or GeminiService(self.config)
        self.citation_engine = citation_engine or CitationEngine()
        self.prompt_builder = prompt_builder or PromptBuilder()

    def generate_answer(self, evaluation_result: EvidenceEvaluationResult) -> AnswerResult:
        """Generate an evidence-grounded answer with citations and execution metrics."""
        pipeline_start = time.perf_counter()
        query = evaluation_result.query_analysis.query
        decision = evaluation_result.evidence_decision
        confidence = evaluation_result.confidence_score

        # Step 9: Log incoming query, evidence confidence, decision
        log.info(
            "Starting answer generation | query='%s' | decision=%s | confidence=%.2f | chunks=%d",
            query,
            decision.value,
            confidence,
            len(evaluation_result.evaluated_chunks),
        )

        # Build prompts
        system_prompt = self.prompt_builder.get_system_prompt()
        user_prompt = self.prompt_builder.build_user_prompt(evaluation_result)
        prompt_size_chars = len(system_prompt) + len(user_prompt)

        # Step 9: Log prompt size
        log.info("Constructed grounded prompt | total_chars=%d", prompt_size_chars)

        # Step 5: Uncertainty Handling
        # If unsupported, bypass LLM to prevent any potential hallucination
        if decision == EvidenceDecision.UNSUPPORTED:
            log.info("Decision is UNSUPPORTED; bypassing external LLM to prevent hallucination")
            duration_ms = (time.perf_counter() - pipeline_start) * 1000.0

            metrics = AnswerExecutionMetrics(
                llm_latency_ms=0.0,
                prompt_tokens=max(1, prompt_size_chars // 4),
                completion_tokens=40,
                total_tokens=max(1, prompt_size_chars // 4) + 40,
                estimated_cost=0.0,
                response_generation_time_ms=round(duration_ms, 2),
                retrieval_metrics=evaluation_result.retrieval_metrics,
            )

            answer = (
                f"No relevant documentation or evidence was found to answer '{query}'. "
                f"To prevent hallucination, Quorix does not provide unverified information."
            )
            summary = "Query is unsupported by available knowledge sources."
            reasoning = evaluation_result.evaluation_explanation

            # Step 9: Log completion
            log.info(
                "Answer generation completed | response_time=%.2fms | total_tokens=%d",
                duration_ms,
                metrics.total_tokens,
            )

            return AnswerResult(
                answer=answer,
                summary=summary,
                citations=[],
                confidence=confidence,
                evidence_decision=decision,
                reasoning=reasoning,
                execution_metrics=metrics,
            )

        # Invoke Gemini service
        llm_response, token_metrics = self.llm_service.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            evaluation_result=evaluation_result,
        )

        raw_answer = llm_response.get("answer", "")
        summary = llm_response.get("summary", "")
        reasoning = llm_response.get("reasoning", evaluation_result.evaluation_explanation)

        # Step 4: Citation Engine extraction and validation
        citations = self.citation_engine.extract_citations(
            text=raw_answer,
            evaluation_result=evaluation_result,
        )

        pipeline_duration_ms = (time.perf_counter() - pipeline_start) * 1000.0

        # Step 7: Execution Metrics tracking
        metrics = AnswerExecutionMetrics(
            llm_latency_ms=token_metrics.get("llm_latency_ms", 0.0),
            prompt_tokens=token_metrics.get("prompt_tokens", 0),
            completion_tokens=token_metrics.get("completion_tokens", 0),
            total_tokens=token_metrics.get("total_tokens", 0),
            estimated_cost=token_metrics.get("estimated_cost", 0.0),
            response_generation_time_ms=round(pipeline_duration_ms, 2),
            retrieval_metrics=evaluation_result.retrieval_metrics,
        )

        # Step 9: Log response time, token usage, citations
        log.info(
            "Answer generation completed | response_time=%.2fms | llm_latency=%.2fms | "
            "prompt_tokens=%d | completion_tokens=%d | cost=$%.6f | citations_count=%d",
            pipeline_duration_ms,
            metrics.llm_latency_ms,
            metrics.prompt_tokens,
            metrics.completion_tokens,
            metrics.estimated_cost,
            len(citations),
        )

        return AnswerResult(
            answer=raw_answer,
            summary=summary,
            citations=citations,
            confidence=confidence,
            evidence_decision=decision,
            reasoning=reasoning,
            execution_metrics=metrics,
        )

