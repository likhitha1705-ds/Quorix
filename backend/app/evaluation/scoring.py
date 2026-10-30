"""Multi-criterion evidence scoring engine for Phase 5.

Evaluates every retrieved chunk across:
1. Relevance (semantic similarity, keyword overlap, entity overlap, intent alignment)
2. Authority (source type, authoritative credentials, metadata)
3. Freshness (timestamp decay, discounted for historical queries)
4. Directness (whether chunk directly provides the answer to the user query)
"""
from __future__ import annotations

import logging
import math
import re
from datetime import datetime, timezone
from typing import Any

from app.evaluation.config import EvaluationConfig, EvidenceScoringWeights
from app.schemas.evaluation import EvaluatedChunk, EvidenceScore
from app.schemas.intelligence import QueryAnalysis, QueryIntent
from app.schemas.retrieval import RetrievedChunk

log = logging.getLogger(__name__)

STOP_WORDS = {
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "and", "or", "is",
    "are", "was", "were", "what", "why", "how", "when", "which", "who", "whom",
    "with", "by", "from", "about", "into", "through", "after", "before", "between",
}


def _tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric words."""
    return [w for w in re.findall(r"[a-zA-Z0-9_\-\.]+", text.lower()) if len(w) > 1]


class RelevanceEvaluator:
    """Evaluates how well a retrieved chunk answers the query based on semantic and lexical signals."""

    def evaluate(self, chunk: RetrievedChunk, query_analysis: QueryAnalysis) -> float:
        content_lower = chunk.content.lower()
        chunk_tokens = set(_tokenize(chunk.content))

        # 1. Semantic similarity from retrieval
        semantic_score = chunk.similarity_score
        if semantic_score <= 0.0 and chunk.final_score > 0.0:
            semantic_score = chunk.final_score

        # 2. Keyword overlap
        keywords = [k.lower() for k in query_analysis.keywords if k.lower() not in STOP_WORDS]
        if not keywords:
            query_tokens = [t for t in _tokenize(query_analysis.query) if t not in STOP_WORDS]
            keywords = query_tokens

        keyword_overlap = 0.0
        if keywords:
            matched_keywords = sum(1 for kw in keywords if kw in content_lower or kw in chunk_tokens)
            keyword_overlap = min(1.0, matched_keywords / len(keywords))

        # 3. Entity overlap
        entities = [e.lower() for e in query_analysis.entities if e.strip()]
        if entities:
            matched_entities = sum(1 for e in entities if e in content_lower)
            entity_overlap = min(1.0, matched_entities / len(entities))
        else:
            entity_overlap = keyword_overlap

        # 4. Intent alignment
        intent_alignment = self._evaluate_intent_alignment(content_lower, query_analysis.intent)

        # Combine signals
        # If semantic score was not available (e.g. pure keyword test or 0), rebalance to overlap
        if semantic_score <= 0.0:
            relevance = 0.45 * keyword_overlap + 0.35 * entity_overlap + 0.20 * intent_alignment
        else:
            relevance = (
                0.35 * semantic_score
                + 0.30 * keyword_overlap
                + 0.20 * entity_overlap
                + 0.15 * intent_alignment
            )

        return max(0.0, min(1.0, float(relevance)))

    def _evaluate_intent_alignment(self, content: str, intent: QueryIntent) -> float:
        """Score chunk alignment with expected information type for the intent."""
        match intent:
            case QueryIntent.CONFIGURATION_LOOKUP:
                indicators = ["ttl", "timeout", "port", "host", "config", "setting", "parameter", "default", "seconds", "ms", "=", ":"]
                hits = sum(1 for ind in indicators if ind in content)
                return min(1.0, 0.4 + (hits * 0.15))
            case QueryIntent.HISTORICAL_REASON:
                indicators = ["because", "reason", "decision", "introduced", "replaced", "migrated", "deprecated", "originally", "decided", "chose"]
                hits = sum(1 for ind in indicators if ind in content)
                return min(1.0, 0.4 + (hits * 0.15))
            case QueryIntent.BUG_INVESTIGATION:
                indicators = ["error", "bug", "exception", "failed", "fix", "patch", "resolved", "issue", "crash", "reproduce"]
                hits = sum(1 for ind in indicators if ind in content)
                return min(1.0, 0.4 + (hits * 0.15))
            case QueryIntent.IMPLEMENTATION_DETAILS:
                indicators = ["def ", "class ", "function", "return", "impl", "interface", "struct", "import", "call", "endpoint", "api"]
                hits = sum(1 for ind in indicators if ind in content)
                return min(1.0, 0.4 + (hits * 0.15))
            case QueryIntent.TECHNICAL_EXPLANATION:
                indicators = [
                    "architecture", "component", "workflow", "system", "layer", "protocol", "protocols",
                    "overview", "design", "implemented", "spec", "specification", "process", "gateway",
                    "service", "mechanism", "operates", "handles", "runbook"
                ]
                hits = sum(1 for ind in indicators if ind in content)
                return min(1.0, 0.4 + (hits * 0.15))
            case QueryIntent.FEATURE_INFORMATION:
                indicators = [
                    "feature", "capability", "supported", "provides", "version", "option", "allows",
                    "enable", "support", "roadmap", "exploration", "not currently supported"
                ]
                hits = sum(1 for ind in indicators if ind in content)
                return min(1.0, 0.4 + (hits * 0.15))
            case _:
                return 0.5


class AuthorityEvaluator:
    """Evaluates the authority of a retrieved chunk based on source metadata and credentials."""

    def evaluate(self, chunk: RetrievedChunk) -> float:
        meta = chunk.metadata or {}

        # 1. Direct explicit authority score in metadata
        if "authority_score" in meta:
            try:
                return max(0.0, min(1.0, float(meta["authority_score"])))
            except (ValueError, TypeError):
                pass

        if "authority_level" in meta:
            val = meta["authority_level"]
            if isinstance(val, (int, float)):
                return max(0.0, min(1.0, float(val)))
            if isinstance(val, str):
                val_lower = val.lower()
                if val_lower in ("high", "authoritative"):
                    return 0.90
                if val_lower in ("medium", "moderate"):
                    return 0.65
                if val_lower in ("low", "informal"):
                    return 0.40

        # 2. Source type and source name heuristics (Step 3)
        stype = (chunk.source_type or "").lower()
        sname = (chunk.source_name or chunk.source or "").lower()

        if stype in ("document", "documents", "doc"):
            if any(term in sname for term in ("architecture", "official", "rfc", "spec", "standard", "reference")):
                return 0.95
            return 0.88

        if stype in ("conversation", "conversations", "chat"):
            if meta.get("decision") is True or "decision" in sname:
                return 0.75
            return 0.60

        if stype in ("ticket", "tickets", "issue"):
            if meta.get("status", "").lower() in ("closed", "resolved"):
                return 0.70
            return 0.55

        return 0.50


class FreshnessEvaluator:
    """Evaluates timestamp freshness with exponential decay and query-intent discounts."""

    def evaluate(
        self,
        chunk: RetrievedChunk,
        query_analysis: QueryAnalysis,
        half_life_days: float = 180.0,
        historical_penalty_discount: float = 0.25,
    ) -> float:
        ts = chunk.timestamp
        if ts is None and chunk.metadata:
            for field in ("timestamp", "updated_at", "created_at", "last_updated"):
                raw = chunk.metadata.get(field)
                if isinstance(raw, datetime):
                    ts = raw
                    break
                if isinstance(raw, str):
                    try:
                        ts = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                        break
                    except (ValueError, TypeError):
                        continue

        if ts is None:
            # Undated source: return neutral default
            return 0.75

        now = datetime.now(timezone.utc)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        age_seconds = max(0.0, (now - ts).total_seconds())
        age_days = age_seconds / 86400.0

        decay_rate = math.log(2.0) / max(1.0, half_life_days)
        raw_freshness = math.exp(-decay_rate * age_days)

        # Historical queries discount freshness penalty (Step 4)
        if query_analysis.intent == QueryIntent.HISTORICAL_REASON:
            penalty = 1.0 - raw_freshness
            freshness = 1.0 - (penalty * historical_penalty_discount)
        else:
            freshness = raw_freshness

        return max(0.0, min(1.0, float(freshness)))


class DirectnessEvaluator:
    """Evaluates whether the chunk directly answers the question or merely mentions keywords."""

    def evaluate(self, chunk: RetrievedChunk, query_analysis: QueryAnalysis) -> float:
        content_lower = chunk.content.lower()
        intent = query_analysis.intent
        keywords = [k.lower() for k in query_analysis.keywords if k.lower() not in STOP_WORDS]
        entities = [e.lower() for e in query_analysis.entities if e.strip()]

        # Baseline directness
        directness = 0.40

        match intent:
            case QueryIntent.CONFIGURATION_LOOKUP:
                # Directness requires explicit setting assignment or value definition
                has_key_assignment = False
                for term in keywords + entities:
                    # Look for term = value or term: value
                    pattern = rf"\b{re.escape(term)}\b\s*[:=]\s*([a-zA-Z0-9_\-\.]+)"
                    if re.search(pattern, content_lower):
                        has_key_assignment = True
                        break

                if has_key_assignment:
                    directness = 0.95
                elif any(
                    re.search(rf"\b{re.escape(term)}\b\s+(?:is set to|is configured as|defaults? to)\b", content_lower)
                    for term in keywords + entities
                ):
                    directness = 0.90
                elif any(
                    re.search(rf"\b{re.escape(term)}\b\s+is\s+(\d+|true|false)\b", content_lower)
                    for term in keywords + entities
                ):
                    directness = 0.85
                elif any(term in content_lower for term in ("ttl", "timeout", "port", "config", "setting", "parameter")) and any(
                    unit in content_lower for unit in ("seconds", "sec", "ms", "port", "minutes")
                ):
                    directness = 0.70
                elif any(term in content_lower for term in ("configuration", "setting", "parameter", "config")):
                    directness = 0.50
                elif any(term in content_lower for term in keywords + entities):
                    directness = 0.30
                else:
                    directness = 0.20

            case QueryIntent.HISTORICAL_REASON:
                # Directness requires causal statements or decision rationales
                causal_patterns = [
                    r"(?:because|reason for|introduced to|decided to|in order to|migrated from|switched to)",
                    r"(?:rationale|motivation|goal was|chosen over|instead of)",
                ]
                has_causal = any(re.search(pat, content_lower) for pat in causal_patterns)
                relevant_entity_present = any(e in content_lower for e in entities) if entities else True

                if has_causal and relevant_entity_present:
                    directness = 0.92
                elif has_causal:
                    directness = 0.75
                elif relevant_entity_present:
                    directness = 0.55
                else:
                    directness = 0.35

            case QueryIntent.BUG_INVESTIGATION:
                # Directness requires root cause, fix description, or stack trace resolution
                fix_patterns = [
                    r"(?:root cause|fixed by|workaround|resolution|resolved in|patch|bug fix|solution is)",
                    r"(?:fixed issue|addresses bug|reproduced by|mitigation)",
                ]
                has_fix = any(re.search(pat, content_lower) for pat in fix_patterns)
                if has_fix:
                    directness = 0.95
                elif "error" in content_lower or "exception" in content_lower:
                    directness = 0.65
                else:
                    directness = 0.40

            case QueryIntent.IMPLEMENTATION_DETAILS:
                has_code = "```" in chunk.content or any(term in content_lower for term in ("def ", "class ", "function ", "return "))
                if has_code:
                    directness = 0.90
                elif any(e in content_lower for e in entities):
                    directness = 0.70
                else:
                    directness = 0.45

            case QueryIntent.TECHNICAL_EXPLANATION:
                explain_patterns = [
                    r"(?:is implemented using|implemented with|utilizes|works by|consists of|operates via|issues|manages|handles|designed to)",
                    r"(?:specification|spec|architecture|protocol|flow|runbook|process|canary rollouts|access tokens)",
                ]
                has_explain = any(re.search(pat, content_lower) for pat in explain_patterns)
                relevant_entity_present = any(e in content_lower for e in entities) if entities else True
                if has_explain and relevant_entity_present:
                    directness = 0.92
                elif has_explain or relevant_entity_present:
                    directness = 0.75
                else:
                    directness = 0.45

            case QueryIntent.FEATURE_INFORMATION:
                feature_patterns = [
                    r"(?:is not currently supported|not supported|is supported|supported|scheduled for|roadmap|relies on)",
                    r"(?:feature|capability|support)",
                ]
                has_feature = any(re.search(pat, content_lower) for pat in feature_patterns)
                relevant_entity_present = any(e in content_lower for e in entities) if entities else True
                if has_feature and relevant_entity_present:
                    directness = 0.95
                elif has_feature or relevant_entity_present:
                    directness = 0.75
                else:
                    directness = 0.45

            case _:
                # General directness based on keyword density
                if keywords:
                    density = sum(1 for kw in keywords if kw in content_lower) / len(keywords)
                    directness = 0.30 + (density * 0.55)
                else:
                    directness = 0.50

        # Source type affinity modifier
        stype = chunk.source_type.lower() if chunk.source_type else ""
        if intent == QueryIntent.CONFIGURATION_LOOKUP and stype == "document":
            directness = min(1.0, directness + 0.05)
        elif intent == QueryIntent.HISTORICAL_REASON and (stype == "conversation" or "decision" in (chunk.metadata or {})):
            directness = min(1.0, directness + 0.05)

        return max(0.0, min(1.0, float(directness)))


class EvidenceScoringEngine:
    """Dedicated Evidence Scoring Service orchestrating multi-criterion evaluation."""

    def __init__(self, config: EvaluationConfig | None = None) -> None:
        self.config = config or EvaluationConfig()
        self.relevance_evaluator = RelevanceEvaluator()
        self.authority_evaluator = AuthorityEvaluator()
        self.freshness_evaluator = FreshnessEvaluator()
        self.directness_evaluator = DirectnessEvaluator()

    def score_chunk(self, chunk: RetrievedChunk, query_analysis: QueryAnalysis) -> EvaluatedChunk:
        """Evaluate a single retrieved chunk and calculate its confidence score."""
        relevance = self.relevance_evaluator.evaluate(chunk, query_analysis)
        authority = self.authority_evaluator.evaluate(chunk)
        freshness = self.freshness_evaluator.evaluate(
            chunk,
            query_analysis,
            half_life_days=self.config.freshness_half_life_days,
            historical_penalty_discount=self.config.historical_penalty_discount,
        )
        directness = self.directness_evaluator.evaluate(chunk, query_analysis)

        weights = self.config.weights
        confidence = (
            weights.relevance * relevance
            + weights.authority * authority
            + weights.directness * directness
            + weights.freshness * freshness
        )
        # Low relevance to the query must proportionally discount confidence
        if relevance < 0.25:
            confidence = confidence * (relevance / 0.25)
        confidence = max(0.0, min(1.0, float(confidence)))

        explanation = self._build_chunk_explanation(
            chunk=chunk,
            relevance=relevance,
            authority=authority,
            directness=directness,
            freshness=freshness,
            confidence=confidence,
        )

        evidence_score = EvidenceScore(
            relevance_score=round(relevance, 4),
            authority_score=round(authority, 4),
            freshness_score=round(freshness, 4),
            directness_score=round(directness, 4),
            confidence_score=round(confidence, 4),
            explanation=explanation,
        )

        return EvaluatedChunk(
            chunk=chunk,
            evidence_score=evidence_score,
        )

    def _build_chunk_explanation(
        self,
        chunk: RetrievedChunk,
        relevance: float,
        authority: float,
        directness: float,
        freshness: float,
        confidence: float,
    ) -> str:
        """Synthesize a concise human-readable explanation of the score."""
        auth_desc = "High authority" if authority >= 0.8 else ("Medium authority" if authority >= 0.6 else "Lower authority")
        dir_desc = "direct answer" if directness >= 0.8 else ("partial answer" if directness >= 0.5 else "contextual mention")
        src_name = chunk.source_name or chunk.source or "source"

        return (
            f"{auth_desc} {src_name} providing {dir_desc} "
            f"(rel: {relevance:.2f}, auth: {authority:.2f}, dir: {directness:.2f}, conf: {confidence:.2f})."
        )
