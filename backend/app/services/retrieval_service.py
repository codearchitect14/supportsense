from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.support_kb import SupportKB
from app.services.embedding_service import EmbeddingService


@dataclass(frozen=True)
class RetrievedEntry:
    id: str
    instruction: str
    response: str
    category: str
    intent: str
    similarity: float


class RetrievalService:
    """Embeds a query and runs cosine similarity search against support_kb."""

    def __init__(self, db: Session, embedding_service: EmbeddingService) -> None:
        self._db = db
        self._embedding_service = embedding_service

    def search(self, query: str, *, top_k: int = 5) -> list[RetrievedEntry]:
        query_vector = self._embedding_service.embed_query(query)
        return self.search_by_vector(query_vector, top_k=top_k)

    def search_by_vector(self, query_vector: list[float], *, top_k: int = 5) -> list[RetrievedEntry]:
        # cosine_distance = 1 - cosine_similarity for pgvector's <=> operator.
        distance = SupportKB.embedding.cosine_distance(query_vector)
        rows = (
            self._db.query(SupportKB, distance.label("distance"))
            .filter(SupportKB.embedding.is_not(None))
            .order_by(distance)
            .limit(top_k)
            .all()
        )

        return [
            RetrievedEntry(
                id=str(row.SupportKB.id),
                instruction=row.SupportKB.instruction,
                response=row.SupportKB.response,
                category=row.SupportKB.category,
                intent=row.SupportKB.intent,
                similarity=1.0 - row.distance,
            )
            for row in rows
        ]
