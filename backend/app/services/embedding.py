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
                try:
                    import os
                    os.environ["TOKENIZERS_PARALLELISM"] = "false"
                    os.environ["OMP_NUM_THREADS"] = "1"
                    os.environ["MKL_NUM_THREADS"] = "1"
                    try:
                        import torch
                        torch.set_num_threads(1)
                    except Exception:
                        pass
                    from sentence_transformers import SentenceTransformer  # lazy import

                    log.info("Loading embedding model %s", self.model_name)
                    self._model = SentenceTransformer(self.model_name)
                except Exception as exc:
                    log.warning("Could not load sentence_transformers (%s); falling back to BM25 retrieval", exc)
                    self._model = None
        return self._model

    @property
    def dimension(self) -> int:
        if self.model is not None:
            try:
                dim = self.model.get_sentence_embedding_dimension()
                if dim:
                    return int(dim)
            except Exception:
                pass
        return 384

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self.model is None:
            return []
        try:
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
        except Exception as exc:
            log.warning("Failed to embed documents with sentence-transformers (%s)", exc)
            return []
