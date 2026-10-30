"""Conflict detection engine for Step 7 of Phase 5.

Identifies factual contradictions, configuration discrepancies, and architectural
divergences across retrieved sources without discarding contradictory evidence.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from app.schemas.evaluation import Conflict, EvaluatedChunk

log = logging.getLogger(__name__)

# Mutually exclusive architectural components for technology contradiction detection
EXCLUSIVE_TECH_CATEGORIES: dict[str, set[str]] = {
    "message_broker": {"kafka", "rabbitmq", "pulsar", "activemq", "sqs"},
    "cache_layer": {"redis", "memcached", "hazelcast"},
    "database": {"postgresql", "postgres", "mysql", "mongodb", "cassandra", "dynamodb"},
    "api_style": {"graphql", "grpc", "rest", "soap"},
    "search_engine": {"elasticsearch", "opensearch", "solr", "qdrant"},
}

# Regex to extract key-value configuration assignments
CONFIG_PATTERNS = [
    re.compile(
        r"\b(?P<key>[a-zA-Z0-9_\-\.]+)\s*(?:=|:|is set to|set to|configured as|defaults? to)\s*(?P<val>[a-zA-Z0-9_\-\./]+(?:\s*(?:seconds|sec|s|ms|minutes|min|m|hours|hrs|h|mb|gb|kb))?)",
        re.IGNORECASE,
    ),
]


class ConflictDetector:
    """Detects configuration, architectural, and polarity contradictions between chunks."""

    def __init__(self, min_confidence_for_high_severity: float = 0.60) -> None:
        self.min_confidence_for_high_severity = min_confidence_for_high_severity

    def detect(self, evaluated_chunks: list[EvaluatedChunk]) -> list[Conflict]:
        """Examine all pairs of evaluated chunks and return detected conflicts."""
        if len(evaluated_chunks) < 2:
            return []

        conflicts: list[Conflict] = []
        seen_pairs: set[tuple[str, str, str]] = set()

        # 1. Extract parsed configurations and tech indicators for all chunks
        chunk_configs = [self._extract_configs(c) for c in evaluated_chunks]
        chunk_techs = [self._extract_technologies(c) for c in evaluated_chunks]
        chunk_polarities = [self._extract_polarities(c) for c in evaluated_chunks]

        # 2. Compare pairs
        for i in range(len(evaluated_chunks)):
            for j in range(i + 1, len(evaluated_chunks)):
                c1, c2 = evaluated_chunks[i], evaluated_chunks[j]

                # (a) Check configuration discrepancies
                conf_conflicts = self._detect_config_discrepancies(
                    c1, c2, chunk_configs[i], chunk_configs[j], seen_pairs
                )
                conflicts.extend(conf_conflicts)

                # (b) Check architectural contradictions
                arch_conflicts = self._detect_architectural_contradictions(
                    c1, c2, chunk_techs[i], chunk_techs[j], seen_pairs
                )
                conflicts.extend(arch_conflicts)

                # (c) Check polarity contradictions
                polarity_conflicts = self._detect_polarity_contradictions(
                    c1, c2, chunk_polarities[i], chunk_polarities[j], seen_pairs
                )
                conflicts.extend(polarity_conflicts)

        return conflicts

    def _extract_configs(self, evaluated: EvaluatedChunk) -> dict[str, str]:
        """Extract key-value parameters declared in chunk content."""
        configs: dict[str, str] = {}
        content = evaluated.content

        for pattern in CONFIG_PATTERNS:
            for match in pattern.finditer(content):
                key = match.group("key").strip().lower()
                val = match.group("val").strip().lower()

                # Filter out obvious false positives (common english words captured as keys)
                if key in {"the", "this", "that", "there", "it", "note", "example", "version", "in", "on", "at"}:
                    continue
                # Normalize time units if numeric
                norm_val = self._normalize_config_val(val)
                configs[key] = norm_val

        return configs

    def _normalize_config_val(self, val: str) -> str:
        """Normalize config value strings for clean comparison."""
        v = val.strip().lower()
        # Remove trailing punctuation
        v = re.sub(r"[\.,;]+$", "", v)
        # Normalize seconds: e.g. "300 seconds" -> "300s", "300 s" -> "300s"
        v = re.sub(r"\s*(seconds|second|sec)\b", "s", v)
        v = re.sub(r"\s*(minutes|minute|min)\b", "m", v)
        v = re.sub(r"\s*(hours|hour|hr|hrs)\b", "h", v)
        v = re.sub(r"\s*(milliseconds|millisec|ms)\b", "ms", v)
        return v

    def _detect_config_discrepancies(
        self,
        c1: EvaluatedChunk,
        c2: EvaluatedChunk,
        configs1: dict[str, str],
        configs2: dict[str, str],
        seen_pairs: set[tuple[str, str, str]],
    ) -> list[Conflict]:
        """Find keys present in both chunks with different values."""
        conflicts = []
        common_keys = set(configs1.keys()) & set(configs2.keys())

        for key in common_keys:
            v1, v2 = configs1[key], configs2[key]
            if v1 != v2:
                pair_id = (min(c1.chunk_id, c2.chunk_id), max(c1.chunk_id, c2.chunk_id), f"config:{key}")
                if pair_id in seen_pairs:
                    continue
                seen_pairs.add(pair_id)

                severity = self._compute_severity(c1, c2)
                explanation = (
                    f"Configuration conflict detected for '{key}': "
                    f"'{c1.source}' specifies '{v1}' (conf: {c1.score:.2f}), whereas "
                    f"'{c2.source}' specifies '{v2}' (conf: {c2.score:.2f})."
                )
                conflicts.append(
                    Conflict(
                        conflicting_chunks=[c1.chunk_id, c2.chunk_id],
                        conflicting_fields=[key],
                        severity=severity,
                        explanation=explanation,
                    )
                )

        return conflicts

    def _extract_technologies(self, evaluated: EvaluatedChunk) -> dict[str, str]:
        """Extract mentioned technologies categorized by functional domain."""
        content_lower = evaluated.content.lower()
        matched: dict[str, str] = {}

        for category, tech_set in EXCLUSIVE_TECH_CATEGORIES.items():
            for tech in tech_set:
                # Word boundary match
                if re.search(rf"\b{re.escape(tech)}\b", content_lower):
                    # Check context: is it declared as used/implemented?
                    decl_pattern = rf"\b(?:using|uses|used|implemented with|migrated to|chose|standardized on)\s+(?:the\s+)?{re.escape(tech)}\b"
                    if re.search(decl_pattern, content_lower) or tech in content_lower:
                        matched[category] = tech
                        break

        return matched

    def _detect_architectural_contradictions(
        self,
        c1: EvaluatedChunk,
        c2: EvaluatedChunk,
        tech1: dict[str, str],
        tech2: dict[str, str],
        seen_pairs: set[tuple[str, str, str]],
    ) -> list[Conflict]:
        """Find mutually exclusive technology selections declared across chunks."""
        conflicts = []
        common_categories = set(tech1.keys()) & set(tech2.keys())

        for cat in common_categories:
            t1, t2 = tech1[cat], tech2[cat]
            if t1 != t2:
                pair_id = (min(c1.chunk_id, c2.chunk_id), max(c1.chunk_id, c2.chunk_id), f"tech:{cat}")
                if pair_id in seen_pairs:
                    continue
                seen_pairs.add(pair_id)

                severity = self._compute_severity(c1, c2)
                explanation = (
                    f"Architectural contradiction detected for '{cat}': "
                    f"'{c1.source}' asserts use of {t1.upper()} (conf: {c1.score:.2f}), while "
                    f"'{c2.source}' asserts use of {t2.upper()} (conf: {c2.score:.2f})."
                )
                conflicts.append(
                    Conflict(
                        conflicting_chunks=[c1.chunk_id, c2.chunk_id],
                        conflicting_fields=[cat],
                        severity=severity,
                        explanation=explanation,
                    )
                )

        return conflicts

    def _extract_polarities(self, evaluated: EvaluatedChunk) -> dict[str, str]:
        """Extract enabled/disabled or supported/deprecated status on features."""
        content_lower = evaluated.content.lower()
        polarities: dict[str, str] = {}

        # Look for '<feature> is enabled' vs '<feature> is disabled'
        pos_match = re.finditer(r"\b([a-zA-Z0-9_\-]+)\s+is\s+(?:enabled|supported|active|recommended|mandatory)\b", content_lower)
        for m in pos_match:
            feature = m.group(1).lower()
            if feature not in {"this", "that", "it", "feature"}:
                polarities[feature] = "enabled"

        neg_match = re.finditer(r"\b([a-zA-Z0-9_\-]+)\s+is\s+(?:disabled|unsupported|deprecated|inactive|forbidden)\b", content_lower)
        for m in neg_match:
            feature = m.group(1).lower()
            if feature not in {"this", "that", "it", "feature"}:
                polarities[feature] = "disabled"

        return polarities

    def _detect_polarity_contradictions(
        self,
        c1: EvaluatedChunk,
        c2: EvaluatedChunk,
        pol1: dict[str, str],
        pol2: dict[str, str],
        seen_pairs: set[tuple[str, str, str]],
    ) -> list[Conflict]:
        """Find features with opposing polarities (enabled vs disabled)."""
        conflicts = []
        common_features = set(pol1.keys()) & set(pol2.keys())

        for feat in common_features:
            p1, p2 = pol1[feat], pol2[feat]
            if p1 != p2:
                pair_id = (min(c1.chunk_id, c2.chunk_id), max(c1.chunk_id, c2.chunk_id), f"polarity:{feat}")
                if pair_id in seen_pairs:
                    continue
                seen_pairs.add(pair_id)

                severity = self._compute_severity(c1, c2)
                explanation = (
                    f"Polarity conflict detected for '{feat}': "
                    f"'{c1.source}' states '{feat} is {p1}', whereas "
                    f"'{c2.source}' states '{feat} is {p2}'."
                )
                conflicts.append(
                    Conflict(
                        conflicting_chunks=[c1.chunk_id, c2.chunk_id],
                        conflicting_fields=[feat],
                        severity=severity,
                        explanation=explanation,
                    )
                )

        return conflicts

    def _compute_severity(self, c1: EvaluatedChunk, c2: EvaluatedChunk) -> str:
        """Compute conflict severity based on chunk confidence levels."""
        s1, s2 = c1.score, c2.score
        threshold = self.min_confidence_for_high_severity

        if s1 >= threshold and s2 >= threshold:
            return "high"
        if s1 >= threshold or s2 >= threshold:
            return "medium"
        return "low"

