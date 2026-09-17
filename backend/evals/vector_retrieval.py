from __future__ import annotations

from collections.abc import Callable, Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from app.services.semantic_search_service import search_project_chunks


RetrievalFunction = Callable[
    [str, int],
    Sequence[str],
]


def build_vector_retriever(
    db: Session,
    project_id: UUID,
) -> RetrievalFunction:
    """
    Crea un adaptador entre el retrieval vectorial real de DevPilot
    y el contrato utilizado por el sistema de evaluación.

    El resultado conserva el orden original de los chunks recuperados.
    No se eliminan rutas duplicadas deliberadamente, ya que queremos
    medir el comportamiento real del retrieval actual.
    """

    def retrieve(
        question: str,
        k: int,
    ) -> list[str]:
        results = search_project_chunks(
            db=db,
            project_id=project_id,
            query=question,
            top_k=k,
        )

        return [
            result.path
            for result in results
        ]

    return retrieve