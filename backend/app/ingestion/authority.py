"""Rule-based authority levels (0-1). Deterministic; no LLM involved."""
from __future__ import annotations

from typing import Any

from app.schemas.source import SourceType

SOURCE_DEFAULTS: dict[SourceType, float] = {
    SourceType.DOCUMENT: 0.85,
    SourceType.CONVERSATION: 0.5,
    SourceType.TICKET: 0.6,
}

# (source_type, status) -> (level, basis)
_STATUS_RULES: dict[tuple[SourceType, str], tuple[float, str]] = {
    (SourceType.DOCUMENT, "approved"): (0.9, "approved documentation"),
    (SourceType.DOCUMENT, "draft"): (0.5, "draft documentation"),
    (SourceType.DOCUMENT, "deprecated"): (0.3, "deprecated documentation"),
    (SourceType.TICKET, "closed"): (0.7, "closed ticket"),
    (SourceType.TICKET, "resolved"): (0.7, "resolved ticket"),
    (SourceType.TICKET, "in_progress"): (0.55, "in-progress ticket"),
    (SourceType.TICKET, "open"): (0.45, "open ticket"),
    (SourceType.TICKET, "wontfix"): (0.3, "won't-fix ticket"),
}


def resolve_authority(
    source_type: SourceType,
    status: str | None,
    metadata: dict[str, Any],
    explicit: float | None = None,
) -> tuple[float, str]:
    """Explicit level in the record wins; otherwise rules; otherwise source default."""
    if explicit is not None:
        return explicit, "explicit in source record"
    if source_type == SourceType.CONVERSATION:
        if metadata.get("decision") is True:
            return 0.7, "conversation recording a team decision"
        return SOURCE_DEFAULTS[source_type], "informal conversation"
    if status:
        rule = _STATUS_RULES.get((source_type, status.lower()))
        if rule:
            return rule
    return SOURCE_DEFAULTS[source_type], f"default for {source_type.value}"
