from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from evals.diversified_vector_retrieval import (
    build_diversified_vector_retriever,
)
from evals.lexical_retrieval import (
    build_lexical_retriever,
)
from evals.retrieval_metrics import normalize_path


DEFAULT_VECTOR_CANDIDATE_K = 20
DEFAULT_LEXICAL_CANDIDATE_K = 20
DEFAULT_RRF_K = 60
DEFAULT_VECTOR_WEIGHT = 1.0
DEFAULT_LEXICAL_WEIGHT = 1.0


RetrievalFunction = Callable[
    [str, int],
    Sequence[str],
]


@dataclass(frozen=True)
class HybridSearchResult:
    path: str
    score: float
    vector_rank: int | None
    lexical_rank: int | None


def reciprocal_rank_fusion(
    vector_files: Sequence[str],
    lexical_files: Sequence[str],
    *,
    final_k: int,
    rrf_k: int = DEFAULT_RRF_K,
    vector_weight: float = DEFAULT_VECTOR_WEIGHT,
    lexical_weight: float = DEFAULT_LEXICAL_WEIGHT,
) -> list[HybridSearchResult]:
    """
    Fusiona dos rankings mediante Weighted Reciprocal Rank Fusion.

    score(d) =
        vector_weight / (rrf_k + vector_rank)
        +
        lexical_weight / (rrf_k + lexical_rank)

    Los pesos por defecto son 1.0 / 1.0, por lo que el
    comportamiento sigue siendo equivalente al RRF original.
    """
    if final_k <= 0:
        raise ValueError(
            "final_k must be greater than zero"
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

    scores: dict[str, float] = {}
    paths: dict[str, str] = {}
    vector_ranks: dict[str, int] = {}
    lexical_ranks: dict[str, int] = {}

    for rank, path in enumerate(
        vector_files,
        start=1,
    ):
        normalized = normalize_path(
            path
        )

        paths.setdefault(
            normalized,
            path,
        )

        vector_ranks.setdefault(
            normalized,
            rank,
        )

        scores[normalized] = (
            scores.get(
                normalized,
                0.0,
            )
            + vector_weight
            / (
                rrf_k + rank
            )
        )

    for rank, path in enumerate(
        lexical_files,
        start=1,
    ):
        normalized = normalize_path(
            path
        )

        paths.setdefault(
            normalized,
            path,
        )

        lexical_ranks.setdefault(
            normalized,
            rank,
        )

        scores[normalized] = (
            scores.get(
                normalized,
                0.0,
            )
            + lexical_weight
            / (
                rrf_k + rank
            )
        )

    ranked_paths = sorted(
        scores,
        key=lambda normalized: (
            -scores[normalized],
            min(
                vector_ranks.get(
                    normalized,
                    10**9,
                ),
                lexical_ranks.get(
                    normalized,
                    10**9,
                ),
            ),
            normalized,
        ),
    )

    return [
        HybridSearchResult(
            path=paths[normalized],
            score=scores[normalized],
            vector_rank=vector_ranks.get(
                normalized
            ),
            lexical_rank=lexical_ranks.get(
                normalized
            ),
        )
        for normalized in ranked_paths[:final_k]
    ]


def build_hybrid_retriever(
    db: Session,
    project_id: UUID,
    *,
    vector_candidate_k: int = DEFAULT_VECTOR_CANDIDATE_K,
    lexical_candidate_k: int = DEFAULT_LEXICAL_CANDIDATE_K,
    rrf_k: int = DEFAULT_RRF_K,
    vector_weight: float = DEFAULT_VECTOR_WEIGHT,
    lexical_weight: float = DEFAULT_LEXICAL_WEIGHT,
) -> RetrievalFunction:
    """
    Construye el retrieval híbrido de DevPilot AI.
    """
    if vector_candidate_k <= 0:
        raise ValueError(
            "vector_candidate_k must be greater than zero"
        )

    if lexical_candidate_k <= 0:
        raise ValueError(
            "lexical_candidate_k must be greater than zero"
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

    vector_retrieve = (
        build_diversified_vector_retriever(
            db=db,
            project_id=project_id,
            candidate_k=vector_candidate_k,
        )
    )

    lexical_retrieve = (
        build_lexical_retriever(
            db=db,
            project_id=project_id,
            candidate_k=lexical_candidate_k,
        )
    )

    def retrieve(
        question: str,
        k: int,
    ) -> list[str]:
        if k <= 0:
            raise ValueError(
                "k must be greater than zero"
            )

        vector_files = vector_retrieve(
            question,
            vector_candidate_k,
        )

        lexical_files = lexical_retrieve(
            question,
            lexical_candidate_k,
        )

        fused_results = reciprocal_rank_fusion(
            vector_files=vector_files,
            lexical_files=lexical_files,
            final_k=k,
            rrf_k=rrf_k,
            vector_weight=vector_weight,
            lexical_weight=lexical_weight,
        )

        return [
            result.path
            for result in fused_results
        ]

    return retrieve