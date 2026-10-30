"""Retrieval adapters package."""
from __future__ import annotations

from app.retrieval.adapters.base import BaseRetrievalAdapter
from app.retrieval.adapters.conversations import ConversationRetrievalAdapter
from app.retrieval.adapters.documents import DocumentRetrievalAdapter
from app.retrieval.adapters.tickets import TicketRetrievalAdapter


class RetrievalAdapterRegistry:
    """Registry mapping source types ('document', 'conversation', 'ticket') to adapters."""

    def __init__(self, adapters: list[BaseRetrievalAdapter] | None = None) -> None:
        self._adapters: dict[str, BaseRetrievalAdapter] = {}
        if adapters:
            for a in adapters:
                self.register(a)

    def register(self, adapter: BaseRetrievalAdapter) -> None:
        self._adapters[adapter.source_type.lower()] = adapter

    def get_adapter(self, source_type: str) -> BaseRetrievalAdapter | None:
        return self._adapters.get(source_type.lower())


__all__ = [
    "BaseRetrievalAdapter",
    "DocumentRetrievalAdapter",
    "ConversationRetrievalAdapter",
    "TicketRetrievalAdapter",
    "RetrievalAdapterRegistry",
]

