import logging
import threading

from sentence_transformers import SentenceTransformer

from app.core.settings import settings

logger = logging.getLogger("app.embedding")

# bge models are trained to prepend this instruction to queries (not to the
# passages being searched), which measurably improves retrieval quality.
_QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "


class EmbeddingService:
    """Loads the embedding model once and exposes embed methods for queries and passages.

    Runs on CPU, which is sufficient for the small models this project uses
    (BAAI/bge-small-en-v1.5 or all-MiniLM-L6-v2), so no GPU/API cost is
    required for embeddings.
    """

    def __init__(self, model_name: str) -> None:
        logger.info("loading embedding model", extra={"model": model_name})
        self._model = SentenceTransformer(model_name, device="cpu")
        self.dimension = self._model.get_embedding_dimension()

    def embed_passage(self, text: str) -> list[float]:
        return self._model.encode(text, normalize_embeddings=True).tolist()

    def embed_passages(self, texts: list[str]) -> list[list[float]]:
        return self._model.encode(texts, normalize_embeddings=True).tolist()

    def embed_query(self, text: str) -> list[float]:
        return self._model.encode(_QUERY_INSTRUCTION + text, normalize_embeddings=True).tolist()


_instance: EmbeddingService | None = None
_lock = threading.Lock()


def get_embedding_service() -> EmbeddingService:
    global _instance
    if _instance is None:
        with _lock:
            if _instance is None:
                _instance = EmbeddingService(settings.embedding_model)
    return _instance
