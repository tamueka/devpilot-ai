from __future__ import annotations

from collections.abc import Callable, Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from app.services.semantic_search_service import search_project_chunks
from evals.retrieval_metrics import normalize_path


DEFAULT_CHUNK_CANDIDATE_K = 100


RetrievalFunction = Callable[
    [str, int],
    Sequence[str],
]


def build_vector_candidate_retriever(
    db: Session,
    project_id: UUID,
    *,
    chunk_candidate_k: int = DEFAULT_CHUNK_CANDIDATE_K,
) -> RetrievalFunction:
    """
    Construye un retriever orientado a generar candidatos
    documentales para fusión híbrida o reranking.

    A diferencia del baseline vectorial diversificado:

        top 20 chunks
            ↓
        pocos documentos únicos

    esta estrategia realiza oversampling de chunks:

        top 100 chunks
            ↓
        deduplicación por documento
            ↓
        hasta K documentos únicos

    El ranking relativo original de pgvector se conserva.
    """

    if chunk_candidate_k <= 0:
        raise ValueError(
            "chunk_candidate_k must be greater than zero"
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
            chunk_candidate_k,
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