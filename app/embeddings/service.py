from __future__ import annotations

from app.embeddings.encoder import EmbeddingEncoder
from app.utils.text_processing import build_embedding_document


class EmbeddingService:
    def __init__(self):
        self.encoder = EmbeddingEncoder()

    def generate(
        self,
        title: str,
        root_cause: str,
        fix: str,
        symptoms: list[str],
        tags: list[str] | None = None,
    ) -> list[float]:
        doc = build_embedding_document(title, root_cause, fix, symptoms, tags)
        return self.encoder.encode(doc)

    def generate_query_embedding(self, query: str) -> list[float]:
        return self.encoder.encode(query)
