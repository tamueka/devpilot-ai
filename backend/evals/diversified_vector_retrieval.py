from __future__ import annotations

from collections.abc import Callable, Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from app.services.semantic_search_service import search_project_chunks
from evals.retrieval_metrics import normalize_path


DEFAULT_CANDIDATE_K = 20


RetrievalFunction = Callable[
    [str, int],
    Sequence[str],
]


def build_diversified_vector_retriever(
    db: Session,
    project_id: UUID,
    *,
    candidate_k: int = DEFAULT_CANDIDATE_K,
) -> RetrievalFunction:
    """
    Construye un retriever vectorial con diversificación por documento.

    Estrategia:
    1. Recuperar más chunks candidatos que resultados finales.
    2. Mantener el ranking vectorial original.
    3. Eliminar documentos repetidos por path.
    4. Devolver los primeros K documentos únicos.

    No modifica el scoring vectorial ni los embeddings.
    """

    if candidate_k <= 0:
        raise ValueError(
            "candidate_k must be greater than zero"
        )

    def retrieve(
        question: str,
        k: int,
    ) -> list[str]:
        if k <= 0:
            raise ValueError(
                "k must be greater than zero"
            )

        search_top_k = max(
            candidate_k,
            k,
        )

        results = search_project_chunks(
            db=db,
            project_id=project_id,
            query=question,
            top_k=search_top_k,
        )

        unique_paths: list[str] = []
        seen_paths: set[str] = set()

        for result in results:
            normalized_path = normalize_path(
                result.path
            )

            if normalized_path in seen_paths:
                continue

            seen_paths.add(
                normalized_path
            )

            unique_paths.append(
                result.path
            )

            if len(unique_paths) >= k:
                break

        return unique_paths

    return retrieve