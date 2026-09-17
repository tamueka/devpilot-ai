from __future__ import annotations

from collections.abc import Callable, Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from evals.hybrid_retrieval import reciprocal_rank_fusion
from evals.lexical_retrieval import build_lexical_retriever
from evals.vector_candidate_retrieval import (
    DEFAULT_CHUNK_CANDIDATE_K,
    build_vector_candidate_retriever,
)


VECTOR_DOCUMENT_K = 20
LEXICAL_DOCUMENT_K = 20

DEFAULT_RRF_K = 60
DEFAULT_RERANK_CANDIDATE_K = 10

DEFAULT_VECTOR_WEIGHT = 1.0
DEFAULT_LEXICAL_WEIGHT = 1.0


RetrievalFunction = Callable[
    [str, int],
    Sequence[str],
]


def build_reranking_candidate_retriever(
    db: Session,
    project_id: UUID,
    *,
    vector_document_k: int = VECTOR_DOCUMENT_K,
    lexical_document_k: int = LEXICAL_DOCUMENT_K,
    chunk_candidate_k: int = DEFAULT_CHUNK_CANDIDATE_K,
    rrf_k: int = DEFAULT_RRF_K,
    vector_weight: float = DEFAULT_VECTOR_WEIGHT,
    lexical_weight: float = DEFAULT_LEXICAL_WEIGHT,
) -> RetrievalFunction:
    """
    Genera el pool documental previo al reranker.

    Pipeline:

        vector:
            N chunks
                ↓
            documentos únicos

        lexical:
            documentos FTS

                ↓

        Reciprocal Rank Fusion

                ↓

        Top K candidatos para reranking

    El valor experimental recomendado actualmente es K=10.
    """

    if vector_document_k <= 0:
        raise ValueError(
            "vector_document_k must be greater than zero"
        )

    if lexical_document_k <= 0:
        raise ValueError(
            "lexical_document_k must be greater than zero"
        )

    if chunk_candidate_k <= 0:
        raise ValueError(
            "chunk_candidate_k must be greater than zero"
        )

    if rrf_k <= 0:
        raise ValueError(
            "rrf_k must be greater than zero"
        )

    if vector_weight <= 0:
        raise ValueError(
            "vector_weight must be greater than zero"
        )

    if lexical_weight <= 0:
        raise ValueError(
            "lexical_weight must be greater than zero"
        )

    vector_retrieve = build_vector_candidate_retriever(
        db=db,
        project_id=project_id,
        chunk_candidate_k=chunk_candidate_k,
    )

    lexical_retrieve = build_lexical_retriever(
        db=db,
        project_id=project_id,
        candidate_k=lexical_document_k,
    )

    def retrieve(
        question: str,
        k: int,
    ) -> list[str]:
        if k <= 0:
            raise ValueError(
                "k must be greater than zero"
            )

        vector_files = list(
            vector_retrieve(
                question,
                vector_document_k,
            )
        )

        lexical_files = list(
            lexical_retrieve(
                question,
                lexical_document_k,
            )
        )

        fused = reciprocal_rank_fusion(
            vector_files=vector_files,
            lexical_files=lexical_files,
            final_k=k,
            rrf_k=rrf_k,
            vector_weight=vector_weight,
            lexical_weight=lexical_weight,
        )

        return [
            result.path
            for result in fused
        ]

    return retrieve