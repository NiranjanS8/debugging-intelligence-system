from __future__ import annotations

from app.embeddings.service import EmbeddingService


def test_embedding_service_uses_built_document(monkeypatch) -> None:
    captured: dict[str, str] = {}

    class DummyEncoder:
        def encode(self, text: str) -> list[float]:
            captured["text"] = text
            return [0.1, 0.2, 0.3]

    monkeypatch.setattr("app.embeddings.service.EmbeddingEncoder", DummyEncoder)

    service = EmbeddingService()
    vector = service.generate(
        title="React error",
        root_cause="bad binding",
        fix="use arrow",
        symptoms=["crash"],
        tags=["react"],
    )

    assert vector == [0.1, 0.2, 0.3]
    assert "Title: React error" in captured["text"]
    assert "Root Cause: bad binding" in captured["text"]
