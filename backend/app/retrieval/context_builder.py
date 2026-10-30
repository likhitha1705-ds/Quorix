"""Context builder: bounds retrieval context within maximum chunk and token limits."""
from __future__ import annotations

import logging

from app.schemas.retrieval import RetrievalPlan, RetrievedChunk

log = logging.getLogger(__name__)


class ContextBuilder:
    """Builds bounded retrieval context respecting maximum chunk count and token limits."""

    def __init__(self, chars_per_token: float = 4.0) -> None:
        self.chars_per_token = chars_per_token

    def build_context(
        self,
        chunks: list[RetrievedChunk],
        plan: RetrievalPlan,
    ) -> tuple[list[RetrievedChunk], int]:
        """Filter and bound chunks according to the retrieval plan limits.

        Returns (bounded_chunks, total_estimated_tokens).
        """
        if not chunks or plan.chunk_limit <= 0 or plan.token_limit <= 0:
            return [], 0

        bounded_chunks: list[RetrievedChunk] = []
        total_tokens = 0

        # Check if the candidate pool has clearly relevant chunks
        has_strong_chunk = any(
            (c.similarity_score >= 0.25 or c.keyword_score > 0.0)
            for c in chunks
        )

        for chunk in chunks:
            # Omit chunks with negligible relevance when strong relevant candidates exist
            if has_strong_chunk and chunk.similarity_score < 0.22 and chunk.keyword_score <= 0.0:
                log.debug("Skipping irrelevant chunk %s (sim=%.3f, kw=%.3f)", chunk.chunk_id, chunk.similarity_score, chunk.keyword_score)
                continue

            # Enforce chunk limit
            if len(bounded_chunks) >= plan.chunk_limit:
                log.debug("Reached chunk limit (%d); stopping context accumulation", plan.chunk_limit)
                break

            chunk_tokens = chunk.estimate_tokens(chars_per_token=self.chars_per_token)

            # Enforce token limit
            if total_tokens + chunk_tokens > plan.token_limit:
                # If we have not added any chunk yet, add this one even if slightly over or truncate
                if not bounded_chunks:
                    bounded_chunks.append(chunk)
                    total_tokens += chunk_tokens
                else:
                    log.debug(
                        "Adding chunk %s (%d tokens) would exceed token limit (%d, current %d); stopping",
                        chunk.chunk_id,
                        chunk_tokens,
                        plan.token_limit,
                        total_tokens,
                    )
                break

            bounded_chunks.append(chunk)
            total_tokens += chunk_tokens

        return bounded_chunks, total_tokens

