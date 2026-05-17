from __future__ import annotations

from sentence_transformers import SentenceTransformer

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        model_name = get_settings().embedding_model
        logger.info(f"Loading embedding model: {model_name}")
        _model = SentenceTransformer(model_name)
        logger.info("Embedding model loaded")
    return _model


class EmbeddingEncoder:
    """Thin wrapper around sentence-transformers for encoding text to vectors."""

    def encode(self, text: str) -> list[float]:
        model = _get_model()
        embedding = model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        model = _get_model()
        embeddings = model.encode(texts, normalize_embeddings=True, batch_size=32)
        return [e.tolist() for e in embeddings]
