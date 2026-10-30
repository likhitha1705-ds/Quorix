"""Sentence Transformers embedding service. The model is loaded lazily, once."""
from __future__ import annotations

import logging
from typing import Any, Callable

log = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(
        self,
        model_name: str,
        batch_size: int = 32,
        model_factory: Callable[[str], Any] | None = None,
    ) -> None:
        self.model_name = model_name
        self.batch_size = batch_size
        self._factory = model_factory
        self._model: Any = None

    @property
    def model(self) -> Any:
        if self._model is None:
            if self._factory is not None:
                self._model = self._factory(self.model_name)
            else:
                from sentence_transformers import SentenceTransformer  # lazy import

                log.info("Loading embedding model %s", self.model_name)
                self._model = SentenceTransformer(self.model_name)
        return self._model

    @property
    def dimension(self) -> int:
        dim = self.model.get_sentence_embedding_dimension()
        if not dim:
            raise RuntimeError(f"Cannot determine embedding dimension for {self.model_name}")
        return int(dim)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self.model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=True,  # cosine distance in Qdrant
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        out = [list(map(float, v)) for v in vectors]
        if any(len(v) != self.dimension for v in out):
            raise RuntimeError("Embedding dimension mismatch")
        return out
