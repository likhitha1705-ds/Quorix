"""Ranking engine: computes fused final_score based on semantic, keyword, authority, and freshness signals."""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

from app.retrieval.config import RankingWeights
from app.schemas.intelligence import QueryIntent
from app.schemas.retrieval import RetrievedChunk


class RankingEngine:
    """Dedicated ranking service combining multi-criterion retrieval signals into a final_score."""

    def __init__(
        self,
        weights: RankingWeights | None = None,
        freshness_half_life_days: float = 180.0,
        historical_penalty_discount: float = 0.25,
    ) -> None:
        self.weights = weights or RankingWeights()
        self.freshness_half_life_days = freshness_half_life_days
        self.historical_penalty_discount = historical_penalty_discount

    def rank(
        self,
        chunks: list[RetrievedChunk],
        intent: QueryIntent | None = None,
        source_authority_map: dict[str, float] | None = None,
        now: datetime | None = None,
    ) -> list[RetrievedChunk]:
        """Score each chunk across all ranking dimensions and return chunks sorted by final_score descending."""
        now = now or datetime.now(timezone.utc)
        ranked_chunks: list[RetrievedChunk] = []

        for chunk in chunks:
            sem_score = chunk.similarity_score
            kw_score = chunk.keyword_score

            # Resolve authority
            auth_score = 0.5
            if source_authority_map and chunk.source_id in source_authority_map:
                auth_score = float(source_authority_map[chunk.source_id])
            elif "authority_level" in chunk.metadata and chunk.metadata["authority_level"] is not None:
                auth_score = float(chunk.metadata["authority_level"])

            # Resolve freshness
            fresh_score = self._compute_freshness(chunk, intent, now)

            # Calculate weighted final score
            final_score = (
                (self.weights.semantic * sem_score)
                + (self.weights.keyword * kw_score)
                + (self.weights.authority * auth_score)
                + (self.weights.freshness * fresh_score)
            )
            final_score = round(max(0.0, min(1.0, final_score)), 4)

            ranked_chunks.append(chunk.model_copy(update={"final_score": final_score}))

        # Sort descending by final_score
        ranked_chunks.sort(key=lambda c: c.final_score, reverse=True)
        return ranked_chunks

    def _compute_freshness(
        self,
        chunk: RetrievedChunk,
        intent: QueryIntent | None,
        now: datetime,
    ) -> float:
        """Compute exponential decay freshness score, discounted for historical queries."""
        ts = chunk.timestamp
        if ts is None:
            raw_ts = chunk.metadata.get("updated_at") or chunk.metadata.get("created_at")
            if isinstance(raw_ts, str):
                try:
                    ts = datetime.fromisoformat(raw_ts)
                except Exception:
                    ts = None
            elif isinstance(raw_ts, datetime):
                ts = raw_ts

        if ts is None:
            return 0.75  # default neutral freshness if unrecorded

        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        delta_days = max(0.0, (now - ts).total_seconds() / 86400.0)
        raw_freshness = math.exp(-math.log(2) * (delta_days / self.freshness_half_life_days))

        if intent == QueryIntent.HISTORICAL_REASON:
            penalty = 1.0 - raw_freshness
            freshness = 1.0 - (penalty * self.historical_penalty_discount)
        else:
            freshness = raw_freshness

        return max(0.0, min(1.0, freshness))

