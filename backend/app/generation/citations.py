"""Citation Engine for Step 4 of Phase 6.

Extracts, validates, deduplicates, and formats citations referencing
retrieved evidence chunks without allowing fabricated sources.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from app.schemas.answer import Citation
from app.schemas.evaluation import EvaluatedChunk, EvidenceEvaluationResult

log = logging.getLogger(__name__)

# Matches citation patterns like [chunk_doc_1], [c1], [doc_1], etc.
CITATION_REGEX = re.compile(r"\[(?:chunk_)?([a-zA-Z0-9_\-]+)\]", re.IGNORECASE)


class CitationEngine:
    """Extracts, validates, and builds citations grounded exclusively in validated evidence."""

    def extract_citations(
        self,
        text: str,
        evaluation_result: EvidenceEvaluationResult,
    ) -> list[Citation]:
        """Extract all valid chunk references from text and map to structured Citations."""
        available_chunks = evaluation_result.evaluated_chunks
        if not available_chunks:
            return []

        # Build chunk lookups (both by exact chunk_id and normalized key)
        chunk_map: dict[str, EvaluatedChunk] = {}
        for c in available_chunks:
            chunk_map[c.chunk_id.lower()] = c
            # Also support 'c1' if chunk_id is 'chunk_1' or vice versa
            chunk_map[c.chunk_id.replace("chunk_", "").lower()] = c

        # Find cited keys in the generated text
        cited_keys: list[str] = []
        for match in CITATION_REGEX.finditer(text):
            key = match.group(1).lower()
            if key in chunk_map and key not in cited_keys:
                cited_keys.append(key)

        citations: list[Citation] = []
        seen_chunk_ids: set[str] = set()

        for key in cited_keys:
            eval_chunk = chunk_map[key]
            if eval_chunk.chunk_id in seen_chunk_ids:
                continue
            seen_chunk_ids.add(eval_chunk.chunk_id)

            citation = self._build_citation(eval_chunk)
            citations.append(citation)

        # Fallback grounding: If text had no explicit bracket tags, but the decision is SUFFICIENT
        # or CONFLICTING, attach citations from strongest supporting evidence
        if not citations and available_chunks:
            # For CONFLICTING, attach all chunks involved in conflicts
            if evaluation_result.conflicts:
                conflict_cids = {cid for conf in evaluation_result.conflicts for cid in conf.conflicting_chunks}
                for c in available_chunks:
                    if c.chunk_id in conflict_cids and c.chunk_id not in seen_chunk_ids:
                        seen_chunk_ids.add(c.chunk_id)
                        citations.append(self._build_citation(c))
            
            # If still empty and decision is SUFFICIENT, attach top strongest evidence
            if not citations and evaluation_result.evidence_summary.strongest_evidence:
                for c in evaluation_result.evidence_summary.strongest_evidence[:3]:
                    if c.chunk_id not in seen_chunk_ids:
                        seen_chunk_ids.add(c.chunk_id)
                        citations.append(self._build_citation(c))

        return citations

    def _build_citation(self, eval_chunk: EvaluatedChunk) -> Citation:
        """Construct a structured Citation object with an informative excerpt quote."""
        chunk = eval_chunk.chunk
        source_name = chunk.source_name or eval_chunk.source or "Knowledge Source"
        source_type = chunk.source_type or "document"
        source_id = chunk.source_id or ""

        # Extract first 160 characters as quote
        raw_content = chunk.content.strip()
        quote = raw_content[:160] + ("..." if len(raw_content) > 160 else "")

        return Citation(
            chunk_id=eval_chunk.chunk_id,
            source_name=source_name,
            source_type=source_type,
            source_id=source_id,
            quote=quote,
            confidence_score=eval_chunk.score,
            metadata=eval_chunk.metadata,
        )

    @staticmethod
    def format_citations_markdown(citations: list[Citation]) -> str:
        """Helper to format citations as a clean markdown block."""
        if not citations:
            return ""

        lines = ["\n### Sources & Citations:"]
        for idx, cit in enumerate(citations, 1):
            quote_str = f' - "{cit.quote}"' if cit.quote else ""
            lines.append(f"{idx}. **{cit.source_name}** ({cit.source_type}) [{cit.chunk_id}]{quote_str}")
        return "\n".join(lines)

