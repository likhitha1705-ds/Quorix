"""Phase 4: Retrieval Budget Manager & Hybrid Retrieval package."""
from __future__ import annotations

from app.retrieval.budget import RetrievalBudgetManager
from app.retrieval.config import RankingWeights, RetrievalConfig
from app.retrieval.context_builder import ContextBuilder
from app.retrieval.deduplication import ChunkDeduplicator
from app.retrieval.engine import HybridRetrievalEngine
from app.retrieval.lexical import LexicalRetrievalEngine
from app.retrieval.metrics import RetrievalMetricsTracker
from app.retrieval.ranking import RankingEngine
from app.retrieval.semantic import SemanticRetrievalEngine
from app.schemas.retrieval import (
    RetrievalBudget,
    RetrievalMetrics,
    RetrievalPlan,
    RetrievalRequest,
    RetrievalResponse,
    RetrievalResult,
    RetrievedChunk,
)

__all__ = [
    "RetrievalConfig",
    "RankingWeights",
    "RetrievalBudgetManager",
    "HybridRetrievalEngine",
    "SemanticRetrievalEngine",
    "LexicalRetrievalEngine",
    "RankingEngine",
    "ChunkDeduplicator",
    "ContextBuilder",
    "RetrievalMetricsTracker",
    "RetrievalBudget",
    "RetrievalPlan",
    "RetrievedChunk",
    "RetrievalMetrics",
    "RetrievalResult",
    "RetrievalRequest",
    "RetrievalResponse",
]

