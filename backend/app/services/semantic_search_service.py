from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Chunk, Document
from app.services.project_embedding_service import create_text_embedding


DEFAULT_TOP_K = 5


@dataclass(frozen=True)
class SemanticSearchResult:
    chunk_id: UUID
    document_id: UUID
    path: str
    language: str
    chunk_index: int
    content: str
    distance: float


def search_project_chunks(
    db: Session,
    project_id: UUID,
    query: str,
    top_k: int = DEFAULT_TOP_K,
) -> list[SemanticSearchResult]:
    if top_k <= 0:
        raise ValueError(
            "top_k debe ser mayor que cero.",
        )

    query_embedding = create_text_embedding(
        query,
    )

    distance = Chunk.embedding.cosine_distance(
        query_embedding,
    ).label("distance")

    statement = (
        select(
            Chunk,
            Document,
            distance,
        )
        .join(
            Document,
            Chunk.document_id == Document.id,
        )
        .where(
            Document.project_id == project_id,
            Chunk.embedding.is_not(None),
        )
        .order_by(distance)
        .limit(top_k)
    )

    rows = db.execute(
        statement,
    ).all()

    return [
        SemanticSearchResult(
            chunk_id=chunk.id,
            document_id=document.id,
            path=document.path,
            language=document.language,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            distance=float(chunk_distance),
        )
        for chunk, document, chunk_distance in rows
    ]