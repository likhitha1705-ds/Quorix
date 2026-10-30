"""Prompt Builder service for Step 2 of Phase 6: Answer Generation & Citation Engine."""
from __future__ import annotations

import json
from typing import Any

from app.schemas.evaluation import EvidenceDecision, EvidenceEvaluationResult

SYSTEM_PROMPT = """You are the Quorix Grounded Answer Generation Engine.
Your sole purpose is to synthesize a factual, precise, and trustworthy response to the user's question using ONLY the validated evidence provided to you.

CRITICAL OPERATIONAL RULES:
1. STRICT EVIDENCE GROUNDING: Use ONLY the provided evidence chunks. NEVER invent, extrapolate, or introduce facts not explicitly stated in the evidence.
2. NO HALLUCINATION: If a fact is not in the evidence chunks, do NOT assume it. Never fabricate citations or reference sources that are not in the provided evidence.
3. INLINE CITATIONS: Every factual assertion you make must cite the supporting evidence chunk ID using bracket format `[chunk_id]` (for example: `[chunk_doc_1]` or `[c1]`). Place the citation immediately following the asserted claim.
4. UNCERTAINTY & DECISION HANDLING:
   - If decision is 'SUFFICIENT': Provide a definitive, clear answer grounded in the high-confidence evidence.
   - If decision is 'CONFLICTING': Directly explain the conflict. State clearly what each conflicting source asserts (with citations), and do not arbitrarily choose one side.
   - If decision is 'INSUFFICIENT': State that the available evidence is insufficient to fully answer the query. Explain what partial information is known and what specific details are missing.
   - If decision is 'UNSUPPORTED': State plainly that no relevant information is available in the knowledge base. Do not fabricate an answer.
5. RESPONSE STRUCTURE: Output your response as a valid JSON object with exactly the following keys:
   {
     "answer": "Comprehensive, evidence-grounded answer with inline [chunk_id] citations.",
     "summary": "1-2 sentence concise executive summary.",
     "reasoning": "Brief explanation of how the evidence supports this response and how uncertainty or conflicts were addressed."
   }
"""


class PromptBuilder:
    """Constructs grounded system and user prompts enforcing strict evidence attribution."""

    @staticmethod
    def get_system_prompt() -> str:
        """Return the immutable system instruction prompt."""
        return SYSTEM_PROMPT.strip()

    @staticmethod
    def build_user_prompt(evaluation_result: EvidenceEvaluationResult) -> str:
        """Construct the dynamic user prompt containing evaluated evidence, decision, and constraints."""
        query = evaluation_result.query_analysis.query
        decision = evaluation_result.evidence_decision
        confidence = evaluation_result.confidence_score
        intent = evaluation_result.query_analysis.intent.value
        conflicts = evaluation_result.conflicts
        chunks = evaluation_result.evaluated_chunks

        # Format conflicts section
        conflict_text = "None detected."
        if conflicts:
            conflict_lines = []
            for idx, c in enumerate(conflicts, 1):
                conflict_lines.append(
                    f"- Conflict {idx} (Severity: {c.severity.upper()} on fields {c.conflicting_fields}): {c.explanation}"
                )
            conflict_text = "\n".join(conflict_lines)

        # Format evidence chunks (prioritize relevant evidence to avoid context poisoning)
        candidate_chunks = [c for c in chunks if c.evidence_score.relevance_score >= 0.25] or chunks[:3]
        chunk_blocks = []
        if not candidate_chunks:
            chunk_blocks.append("No evidence chunks were retrieved.")
        else:
            for c in candidate_chunks:
                chunk_blocks.append(
                    f"--- EVIDENCE CHUNK [{c.chunk_id}] ---\n"
                    f"Source: {c.source} | Source Type: {c.source_type} | Confidence: {c.score:.2f} (Directness: {c.directness_score:.2f}, Authority: {c.authority_score:.2f})\n"
                    f"Content:\n{c.content.strip()}\n"
                )

        chunks_text = "\n".join(chunk_blocks)

        # Guidance instructions tailored to decision
        decision_instruction = ""
        match decision:
            case EvidenceDecision.SUFFICIENT:
                decision_instruction = (
                    "The evidence is SUFFICIENT. Synthesize a definitive, direct answer. "
                    "Ensure every claim has an inline citation pointing to its chunk ID, e.g. [chunk_id]."
                )
            case EvidenceDecision.CONFLICTING:
                decision_instruction = (
                    "The evidence contains CONFLICTING claims. Do not hide the disagreement. "
                    "Clearly state each conflicting position, citing the respective sources and chunk IDs."
                )
            case EvidenceDecision.INSUFFICIENT:
                decision_instruction = (
                    "The evidence is INSUFFICIENT to answer the query completely. "
                    "State the limitations of the current evidence, cite what partial information exists, and identify what is missing."
                )
            case EvidenceDecision.UNSUPPORTED:
                decision_instruction = (
                    "The query is UNSUPPORTED by the retrieved context. "
                    "State that no supporting evidence exists and do not invent an answer."
                )

        prompt = f"""USER QUERY: "{query}"

QUERY INTENT: {intent}
EVALUATION DECISION: {decision.value}
EVALUATION CONFIDENCE: {confidence:.2f}
EVALUATION REASONING: {evaluation_result.evaluation_explanation}

DETECTED CONFLICTS:
{conflict_text}

EVALUATED EVIDENCE:
{chunks_text}

TASK INSTRUCTIONS:
{decision_instruction}
Remember to produce ONLY valid JSON with 'answer', 'summary', and 'reasoning' keys.
"""
        return prompt.strip()

