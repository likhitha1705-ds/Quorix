"""Query Analysis Engine: detects intent, extracts entities and keywords, predicts sources."""
from __future__ import annotations

import logging
import re
from typing import Any

from app.intelligence.config import (
    EXPECTED_INFO_TYPES,
    KNOWN_TECHNICAL_ENTITIES,
    PREFERRED_SOURCES_MAP,
    STOP_WORDS,
)
from app.schemas.intelligence import QueryAnalysis, QueryIntent

log = logging.getLogger(__name__)

# Regular expressions for intent detection
_INTENT_PATTERNS: list[tuple[QueryIntent, list[re.Pattern]]] = [
    (
        QueryIntent.HISTORICAL_REASON,
        [
            re.compile(r"\bwhy\s+(?:was|did|were|have|is|do)\b", re.IGNORECASE),
            re.compile(r"\b(?:historical|rationale|motivation|background|origin)\b", re.IGNORECASE),
            re.compile(r"\breason\s+(?:behind|for|why)\b", re.IGNORECASE),
            re.compile(r"\bwhy\s+.*?\b(?:introduced|added|chosen|deprecated|removed|selected)\b", re.IGNORECASE),
            re.compile(r"\bdecided\s+to\b", re.IGNORECASE),
            re.compile(r"\bdecision\s+(?:behind|record|to|for)\b", re.IGNORECASE),
        ],
    ),
    (
        QueryIntent.CONFIGURATION_LOOKUP,
        [
            re.compile(r"\bhow\s+to\s+configure\b", re.IGNORECASE),
            re.compile(r"\bhow\s+do\s+i\s+(?:set|configure|setup|change|enable)\b", re.IGNORECASE),
            re.compile(r"\b(?:configuration|config|settings?|environment\s+variable|env\s+var)\b", re.IGNORECASE),
            re.compile(r"\b(?:port|credentials|database_url|connection\s+string|parameter|options?)\b", re.IGNORECASE),
            re.compile(r"\bhow\s+to\s+install\b", re.IGNORECASE),
        ],
    ),
    (
        QueryIntent.BUG_INVESTIGATION,
        [
            re.compile(r"\b(?:bug|error|exception|crash|failure|broken|failing|issue|regression)\b", re.IGNORECASE),
            re.compile(r"\b(?:traceback|stacktrace|timeout|nullpointer|connectionerror)\b", re.IGNORECASE),
            re.compile(r"\bfailed\s+to\b", re.IGNORECASE),
            re.compile(r"\bwhy\s+is\s+.*?\b(?:failing|throwing|breaking|crashing|not\s+working)\b", re.IGNORECASE),
            re.compile(r"\bfix\s+for\b", re.IGNORECASE),
            re.compile(r"\bhow\s+to\s+resolve\s+(?:error|issue|bug)\b", re.IGNORECASE),
        ],
    ),
    (
        QueryIntent.IMPLEMENTATION_DETAILS,
        [
            re.compile(r"\bhow\s+is\s+.*?\b(?:implemented|built|structured|written)\b", re.IGNORECASE),
            re.compile(r"\bimplementation\s+(?:details|of)\b", re.IGNORECASE),
            re.compile(r"\b(?:class\s+structure|internal\s+logic|source\s+code|method\s+signature)\b", re.IGNORECASE),
            re.compile(r"\bunder\s+the\s+hood\b", re.IGNORECASE),
            re.compile(r"\bhow\s+does\s+.*?\b(?:handle|process|parse|execute|chunk|embed)\b", re.IGNORECASE),
        ],
    ),
    (
        QueryIntent.FEATURE_INFORMATION,
        [
            re.compile(r"\b(?:does|is)\s+.*?\b(?:support|supported|have)\b", re.IGNORECASE),
            re.compile(r"\bcan\s+(?:quorix|we|the\s+system)\s+.*?\b", re.IGNORECASE),
            re.compile(r"\b(?:feature|features|roadmap|capabilities|enhancement)\b", re.IGNORECASE),
            re.compile(r"\bstatus\s+of\s+(?:feature|support)\b", re.IGNORECASE),
            re.compile(r"\bupcoming\s+feature\b", re.IGNORECASE),
        ],
    ),
    (
        QueryIntent.TECHNICAL_EXPLANATION,
        [
            re.compile(r"\bhow\s+does\s+.*?\bwork\b", re.IGNORECASE),
            re.compile(r"\bwhat\s+is\s+(?:the\s+)?(?:architecture|purpose|flow|concept)\b", re.IGNORECASE),
            re.compile(r"\bexplain\s+(?:the\s+)?", re.IGNORECASE),
            re.compile(r"\boverview\s+of\b", re.IGNORECASE),
            re.compile(r"\bwhat\s+is\b", re.IGNORECASE),
            re.compile(r"\bwhat\s+does\s+.*?\bdo\b", re.IGNORECASE),
        ],
    ),
]

# Common English question starters that shouldn't be counted as entities
_COMMON_QUESTION_STARTERS = {
    "why", "how", "what", "when", "where", "who", "which", "is", "are",
    "does", "do", "did", "can", "could", "should", "would", "has", "have",
    "will", "tell", "explain", "give", "show", "describe",
}


class QueryAnalysisEngine:
    """Dedicated service for natural language query analysis."""

    def __init__(self) -> None:
        pass

    def analyze(self, query: str) -> QueryAnalysis:
        """Analyze a natural language query and return structured QueryAnalysis."""
        cleaned_query = query.strip()
        intent = self.detect_intent(cleaned_query)
        entities = self.extract_entities(cleaned_query)
        keywords = self.extract_keywords(cleaned_query)
        expected_info_type = EXPECTED_INFO_TYPES.get(intent, "general_summary")
        preferred_sources = self.predict_preferred_sources(cleaned_query, intent)

        analysis = QueryAnalysis(
            query=cleaned_query,
            intent=intent,
            keywords=keywords,
            entities=entities,
            expected_information_type=expected_info_type,
            preferred_sources=preferred_sources,
        )
        log.debug("Analyzed query %r -> intent=%s, entities=%s", cleaned_query, intent.value, entities)
        return analysis

    def detect_intent(self, query: str) -> QueryIntent:
        """Detect query intent using weighted pattern matching and heuristics."""
        scored_intents: dict[QueryIntent, int] = {}

        for intent, patterns in _INTENT_PATTERNS:
            for pattern in patterns:
                if pattern.search(query):
                    scored_intents[intent] = scored_intents.get(intent, 0) + 1

        if scored_intents:
            # Pick the intent with the highest pattern hit count
            best_intent = max(scored_intents.items(), key=lambda item: item[1])[0]
            return best_intent

        return QueryIntent.GENERAL_INFORMATION

    def extract_keywords(self, query: str) -> list[str]:
        """Extract meaningful keywords by tokenizing, normalizing, and filtering stop words."""
        # Split tokens preserving alphanumeric and underscores/hyphens
        raw_tokens = re.findall(r"[A-Za-z0-9_\-]+", query)
        keywords: list[str] = []
        seen: set[str] = set()

        for token in raw_tokens:
            token_lower = token.lower().strip("-_")
            if not token_lower or len(token_lower) < 2:
                continue
            if token_lower in STOP_WORDS:
                continue
            if token_lower not in seen:
                seen.add(token_lower)
                keywords.append(token_lower)

        return keywords

    def extract_entities(self, query: str) -> list[str]:
        """Extract named entities, technical concepts, PascalCase/UPPERCASE identifiers."""
        entities: list[str] = []
        seen_lower: set[str] = set()

        # 1. Match known technical entities (case-insensitive)
        for term, canonical in KNOWN_TECHNICAL_ENTITIES.items():
            pattern = rf"\b{re.escape(term)}\b"
            if re.search(pattern, query, re.IGNORECASE):
                if canonical.lower() not in seen_lower:
                    seen_lower.add(canonical.lower())
                    entities.append(canonical)

        # 2. Extract PascalCase or UPPER_CASE words (e.g. ChunkingService, DATABASE_URL, REST)
        id_matches = re.findall(r"\b[A-Z][a-zA-Z0-9_]{2,}\b", query)
        for match in id_matches:
            if match.lower() not in seen_lower and match.lower() not in _COMMON_QUESTION_STARTERS:
                seen_lower.add(match.lower())
                entities.append(match)

        # 3. Extract Capitalized phrases (e.g. "Redis Caching", "Vector Store")
        cap_matches = re.findall(r"\b[A-Z][a-z0-9]+(?:\s+[A-Z][a-z0-9]+)*\b", query)
        for match in cap_matches:
            clean_match = match.strip()
            # If it's a question starter at beginning, skip it
            if clean_match.lower() in _COMMON_QUESTION_STARTERS:
                continue
            if clean_match.lower() not in seen_lower and clean_match.lower() not in STOP_WORDS:
                seen_lower.add(clean_match.lower())
                entities.append(clean_match)

        return entities

    def predict_preferred_sources(self, query: str, intent: QueryIntent) -> list[str]:
        """Predict preferred knowledge source categories based on intent and query hints."""
        # Check if the query spans multiple disparate topics (multi_source check)
        lower_query = query.lower()
        has_doc_hint = any(w in lower_query for w in ["doc", "docs", "spec", "architecture", "reference", "manual"])
        has_conv_hint = any(w in lower_query for w in ["discuss", "team", "meeting", "conversation", "slack", "decision"])
        has_ticket_hint = any(w in lower_query for w in ["bug", "ticket", "issue", "jira", "fix", "pr"])

        matched_hints = sum([has_doc_hint, has_conv_hint, has_ticket_hint])
        if matched_hints >= 2 or intent == QueryIntent.GENERAL_INFORMATION:
            return ["multi_source"]

        return list(PREFERRED_SOURCES_MAP.get(intent, ["multi_source"]))

