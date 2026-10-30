"""Configuration module for Query Analysis & Source Selection."""
from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from app.schemas.intelligence import QueryIntent


class ScoringWeights(BaseModel):
    """Configurable weights for the multi-criteria source scoring algorithm."""

    relevance: float = Field(default=0.35, ge=0.0, le=1.0)
    authority: float = Field(default=0.25, ge=0.0, le=1.0)
    freshness: float = Field(default=0.20, ge=0.0, le=1.0)
    directness: float = Field(default=0.20, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _validate_weights(self) -> "ScoringWeights":
        total = self.relevance + self.authority + self.freshness + self.directness
        if not (0.98 <= total <= 1.02):
            raise ValueError(f"Scoring weights must sum to approximately 1.0 (got {total:.4f})")
        return self


class IntelligenceConfig(BaseModel):
    """Runtime configuration for Phase 3 intelligence layer."""

    weights: ScoringWeights = Field(default_factory=ScoringWeights)
    confidence_threshold: float = Field(default=0.60, ge=0.0, le=1.0)
    min_relevance_threshold: float = Field(default=0.10, ge=0.0, le=1.0)
    max_selected_sources: int = Field(default=3, ge=1)
    freshness_half_life_days: float = Field(default=180.0, gt=0.0)
    historical_penalty_discount: float = Field(default=0.25, ge=0.0, le=1.0)


# Explicit business logic for expected directness (intent x source_type)
DIRECTNESS_SCORES: dict[QueryIntent, dict[str, float]] = {
    QueryIntent.CONFIGURATION_LOOKUP: {
        "document": 0.95,
        "conversation": 0.50,
        "ticket": 0.25,
    },
    QueryIntent.HISTORICAL_REASON: {
        "conversation": 0.95,
        "document": 0.65,
        "ticket": 0.55,
    },
    QueryIntent.TECHNICAL_EXPLANATION: {
        "document": 0.95,
        "conversation": 0.55,
        "ticket": 0.30,
    },
    QueryIntent.BUG_INVESTIGATION: {
        "ticket": 0.95,
        "conversation": 0.80,
        "document": 0.50,
    },
    QueryIntent.FEATURE_INFORMATION: {
        "document": 0.90,
        "ticket": 0.85,
        "conversation": 0.50,
    },
    QueryIntent.IMPLEMENTATION_DETAILS: {
        "document": 0.90,
        "ticket": 0.70,
        "conversation": 0.60,
    },
    QueryIntent.GENERAL_INFORMATION: {
        "document": 0.80,
        "conversation": 0.60,
        "ticket": 0.50,
    },
}

# Mapping from intent to expected information type
EXPECTED_INFO_TYPES: dict[QueryIntent, str] = {
    QueryIntent.TECHNICAL_EXPLANATION: "architectural_explanation",
    QueryIntent.CONFIGURATION_LOOKUP: "configuration_reference",
    QueryIntent.HISTORICAL_REASON: "decision_history",
    QueryIntent.BUG_INVESTIGATION: "incident_troubleshooting",
    QueryIntent.FEATURE_INFORMATION: "feature_specification",
    QueryIntent.IMPLEMENTATION_DETAILS: "code_implementation",
    QueryIntent.GENERAL_INFORMATION: "general_summary",
}

# Preferred source categories per intent
PREFERRED_SOURCES_MAP: dict[QueryIntent, list[str]] = {
    QueryIntent.TECHNICAL_EXPLANATION: ["documents"],
    QueryIntent.CONFIGURATION_LOOKUP: ["documents"],
    QueryIntent.HISTORICAL_REASON: ["conversations", "documents"],
    QueryIntent.BUG_INVESTIGATION: ["tickets", "conversations"],
    QueryIntent.FEATURE_INFORMATION: ["documents", "tickets"],
    QueryIntent.IMPLEMENTATION_DETAILS: ["documents", "tickets"],
    QueryIntent.GENERAL_INFORMATION: ["multi_source"],
}

# Stop words to remove during keyword extraction
STOP_WORDS: set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "can't", "cannot", "could",
    "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down",
    "during", "each", "few", "for", "from", "further", "had", "hadn't", "has",
    "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her",
    "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's",
    "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it",
    "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other",
    "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't",
    "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then",
    "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've",
    "this", "those", "through", "to", "too", "under", "until", "up", "very", "was",
    "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what",
    "what's", "when", "when's", "where", "where's", "which", "while", "who", "who's",
    "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd",
    "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves",
    "tell", "give", "show", "find", "please", "know",
}

# Known domain concepts / entities to recognize even without capitalization
KNOWN_TECHNICAL_ENTITIES: dict[str, str] = {
    "redis": "Redis",
    "caching": "Caching",
    "cache": "Cache",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "qdrant": "Qdrant",
    "docker": "Docker",
    "fastapi": "FastAPI",
    "pydantic": "Pydantic",
    "gemini": "Gemini",
    "jwt": "JWT",
    "oauth": "OAuth",
    "oauth2": "OAuth2",
    "api": "API",
    "rest": "REST",
    "grpc": "gRPC",
    "kafka": "Kafka",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "python": "Python",
    "git": "Git",
    "github": "GitHub",
    "vector": "Vector",
    "embedding": "Embedding",
    "embeddings": "Embeddings",
    "chunking": "Chunking",
    "pipeline": "Pipeline",
    "adapter": "Adapter",
    "ticket": "Ticket",
    "conversation": "Conversation",
    "document": "Document",
    "documents": "Documents",
    "authentication": "Authentication",
    "auth": "Authentication",
    "authorization": "Authorization",
    "oidc": "OpenID Connect",
    "token": "Token",
    "tokens": "Tokens",
    "cookie": "Cookie",
    "session": "Session",
    "deployment": "Deployment",
    "deploy": "Deployment",
    "canary": "Canary Rollout",
    "rollout": "Rollout",
    "argocd": "ArgoCD",
    "cicd": "CI/CD",
    "ci/cd": "CI/CD",
    "runbook": "Runbook",
    "database": "Database",
    "sharding": "Sharding",
    "shard": "Sharding",
    "scaling": "Scaling",
    "pgbouncer": "PgBouncer",
    "replica": "Read Replica",
    "replicas": "Read Replicas",
    "ttl": "TTL",
    "latency": "Latency",
    "sla": "SLA",
    "architecture": "Architecture",
    "adr": "ADR",
}
