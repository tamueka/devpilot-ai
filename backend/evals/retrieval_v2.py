from __future__ import annotations

from collections.abc import Callable, Sequence
from uuid import UUID

from openai import OpenAI
from sqlalchemy.orm import Session

from evals.llm_reranker import (
    DEFAULT_MAX_CHARS_PER_DOCUMENT,
    DEFAULT_RERANK_MODEL,
    rerank_candidate_paths,
)
from evals.multi_source_candidate_retrieval import (
    build_multi_source_candidate_collector,
)
from evals.multi_source_fusion import (
    best_rank_fusion,
)


DEFAULT_RETRIEVAL_V2_CANDIDATE_K = 10
DEFAULT_RETRIEVAL_V2_FINAL_K = 5


RetrievalFunction = Callable[
    [str, int],
    Sequence[str],
]


def build_retrieval_v2_retriever(
    *,
    db: Session,
    project_id: UUID,
    candidate_k: int = DEFAULT_RETRIEVAL_V2_CANDIDATE_K,
    model: str = DEFAULT_RERANK_MODEL,
    max_chars_per_document: int = DEFAULT_MAX_CHARS_PER_DOCUMENT,
    client: OpenAI | None = None,
) -> RetrievalFunction:
    """
    Construye el pipeline Retrieval v2:

        Vector@20
            +
        Lexical@20
            +
        Path@20
            ↓
        Best-Rank Fusion
            ↓
        Top candidate_k
            ↓
        LLM reranker
            ↓
        Top K final

    El valor de K final se recibe en cada llamada al retriever.
    """

    if candidate_k <= 0:
        raise ValueError(
            "candidate_k must be greater than zero"
        )

    if max_chars_per_document <= 0:
        raise ValueError(
            "max_chars_per_document must be greater than zero"
        )

    if not model.strip():
        raise ValueError(
            "model must not be blank"
        )

    collect_candidates = (
        build_multi_source_candidate_collector(
            db=db,
            project_id=project_id,
        )
    )

    def retrieve(
        question: str,
        k: int,
    ) -> list[str]:
        if not question.strip():
            raise ValueError(
                "question must not be blank"
            )

        if k <= 0:
            raise ValueError(
                "k must be greater than zero"
            )

        candidates = collect_candidates(
            question
        )

        fused_candidates = best_rank_fusion(
            candidates,
            final_k=candidate_k,
        )

        candidate_paths = [
            candidate.path
            for candidate in fused_candidates
        ]

        if not candidate_paths:
            return []

        return rerank_candidate_paths(
            db=db,
            project_id=project_id,
            question=question,
            candidate_paths=candidate_paths,
            top_k=k,
            client=client,
            model=model,
            max_chars_per_document=(
                max_chars_per_document
            ),
        )

    return retrieve