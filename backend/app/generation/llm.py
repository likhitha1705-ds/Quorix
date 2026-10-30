"""Gemini LLM Service for Step 1 of Phase 6: Answer Generation & Citation Engine."""
from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any

from app.generation.config import GenerationConfig
from app.schemas.evaluation import EvidenceDecision, EvidenceEvaluationResult

log = logging.getLogger(__name__)


class GeminiService:
    """Reusable Gemini LLM client coordinating grounded response generation and token metrics."""

    def __init__(self, config: GenerationConfig | None = None) -> None:
        self.config = config or GenerationConfig()
        self.client: Any = None
        self._init_client()

    def _init_client(self) -> None:
        """Initialize Google GenAI client if API key is configured."""
        api_key = self.config.api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            log.info("No Gemini API key provided; GeminiService operating in offline grounded mode")
            return

        try:
            from google import genai
            self.client = genai.Client(api_key=api_key)
            log.info("Initialized Google GenAI client for model %s", self.config.model_name)
        except Exception as exc:
            log.warning("Could not initialize google.genai.Client (%s); operating in offline mode", exc)
            self.client = None

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        evaluation_result: EvidenceEvaluationResult,
    ) -> tuple[dict[str, str], dict[str, Any]]:
        """Generate a grounded response respecting system prompt and structured JSON output."""
        start_time = time.perf_counter()

        if self.client is not None:
            try:
                parsed_data, token_metrics = self._call_gemini(system_prompt, user_prompt)
                latency_ms = (time.perf_counter() - start_time) * 1000.0
                token_metrics["llm_latency_ms"] = round(latency_ms, 2)
                return parsed_data, token_metrics
            except Exception as exc:
                log.warning("Gemini API call failed (%s); falling back to offline grounded generator", exc)

        # Fallback to deterministic offline grounded generation
        parsed_data, token_metrics = self._generate_offline(evaluation_result, user_prompt)
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        token_metrics["llm_latency_ms"] = round(latency_ms, 2)
        return parsed_data, token_metrics

    def _call_gemini(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> tuple[dict[str, str], dict[str, Any]]:
        """Invoke live Google GenAI API."""
        from google.genai import types

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=self.config.temperature,
            max_output_tokens=self.config.max_output_tokens,
            response_mime_type="application/json",
        )

        response = self.client.models.generate_content(
            model=self.config.model_name,
            contents=user_prompt,
            config=config,
        )

        raw_text = response.text or "{}"
        parsed = self._parse_json_response(raw_text)

        # Extract token usage
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0

        usage = getattr(response, "usage_metadata", None)
        if usage:
            prompt_tokens = getattr(usage, "prompt_token_count", 0) or 0
            completion_tokens = getattr(usage, "candidates_token_count", 0) or 0
            total_tokens = getattr(usage, "total_token_count", 0) or (prompt_tokens + completion_tokens)
        else:
            prompt_tokens = max(1, len(user_prompt) // 4)
            completion_tokens = max(1, len(raw_text) // 4)
            total_tokens = prompt_tokens + completion_tokens

        cost = self._calculate_cost(prompt_tokens, completion_tokens)

        token_metrics = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost": cost,
        }
        return parsed, token_metrics

    def _generate_offline(
        self,
        evaluation_result: EvidenceEvaluationResult,
        user_prompt: str,
    ) -> tuple[dict[str, str], dict[str, Any]]:
        """Deterministic offline answer generator adhering strictly to evidence and decisions."""
        decision = evaluation_result.evidence_decision
        query = evaluation_result.query_analysis.query
        chunks = evaluation_result.evaluated_chunks

        answer = ""
        summary = ""
        reasoning = evaluation_result.evaluation_explanation

        match decision:
            case EvidenceDecision.SUFFICIENT:
                # Build answer from top chunks with explicit citations
                top_chunks = evaluation_result.evidence_summary.strongest_evidence or chunks[:2]
                if top_chunks:
                    top_rel = max(c.evidence_score.relevance_score for c in top_chunks)
                    min_rel = max(0.40, top_rel * 0.60) if top_rel >= 0.65 else 0.25
                    relevant_chunks = [c for c in top_chunks if c.evidence_score.relevance_score >= min_rel]
                else:
                    relevant_chunks = []
                if not relevant_chunks and top_chunks:
                    relevant_chunks = top_chunks[:1]

                facts = []
                for c in relevant_chunks:
                    content_lines = [line.strip() for line in c.content.strip().split("\n") if line.strip()]
                    chunk_text = " ".join(content_lines[:2]) if len(content_lines) > 1 else (content_lines[0] if content_lines else "")
                    if chunk_text:
                        facts.append(f"{chunk_text} [{c.chunk_id}]")
                answer = " ".join(facts)
                summary = f"Direct and authoritative evidence answers '{query}'."

            case EvidenceDecision.CONFLICTING:
                conflict_explanations = [c.explanation for c in evaluation_result.conflicts]
                c_details = " ".join(conflict_explanations)
                # Include citations for conflicting chunks
                citations_text = " ".join(f"[{c.chunk_id}]" for c in chunks[:2])
                answer = (
                    f"A factual conflict was detected across the retrieved sources. {c_details} {citations_text}"
                )
                summary = "Conflicting evidence prevents a single definitive answer."

            case EvidenceDecision.INSUFFICIENT:
                top = chunks[0] if chunks else None
                partial = f" Partial context was found: '{top.content.strip()[:120]}...' [{top.chunk_id}]." if top else ""
                answer = (
                    f"The available evidence is insufficient to fully answer '{query}'.{partial} "
                    f"Key configuration or historical details remain unverified."
                )
                summary = "Evidence is insufficient to provide a complete answer."

            case EvidenceDecision.UNSUPPORTED:
                answer = (
                    f"No relevant documentation or evidence was found to answer '{query}'. "
                    f"To prevent hallucination, Quorix does not provide unverified information."
                )
                summary = "Query is unsupported by available knowledge sources."

        parsed = {
            "answer": answer,
            "summary": summary,
            "reasoning": reasoning,
        }

        # Estimate tokens
        prompt_tokens = max(1, len(user_prompt) // 4)
        completion_tokens = max(1, (len(answer) + len(summary) + len(reasoning)) // 4)
        total_tokens = prompt_tokens + completion_tokens
        cost = self._calculate_cost(prompt_tokens, completion_tokens)

        token_metrics = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost": cost,
        }
        return parsed, token_metrics

    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate USD cost based on token counts and model pricing."""
        input_cost = (prompt_tokens / 1_000_000.0) * self.config.cost_per_million_input_tokens
        output_cost = (completion_tokens / 1_000_000.0) * self.config.cost_per_million_output_tokens
        return round(input_cost + output_cost, 6)

    @staticmethod
    def _parse_json_response(raw_text: str) -> dict[str, str]:
        """Safely extract and parse JSON object from LLM response text."""
        # Try direct parse
        try:
            return json.loads(raw_text)
        except Exception:
            pass

        # Try markdown code block extraction
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except Exception:
                pass

        # Fallback dictionary
        return {
            "answer": raw_text.strip(),
            "summary": raw_text.strip()[:150],
            "reasoning": "Direct model generation.",
        }
