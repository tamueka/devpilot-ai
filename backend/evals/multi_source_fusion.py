from __future__ import annotations

from dataclasses import dataclass

from evals.multi_source_candidate_retrieval import (
    MultiSourceCandidates,
)
from evals.retrieval_metrics import normalize_path


@dataclass(frozen=True)
class MultiSourceFusionResult:
    path: str

    best_rank: int
    source_count: int
    rank_sum: int

    vector_rank: int | None
    lexical_rank: int | None
    path_rank: int | None


@dataclass
class _MutableRanks:
    path: str

    vector_rank: int | None = None
    lexical_rank: int | None = None
    path_rank: int | None = None


def _register_ranking(
    documents: dict[str, _MutableRanks],
    *,
    paths: tuple[str, ...],
    source: str,
) -> None:
    for rank, path in enumerate(
        paths,
        start=1,
    ):
        normalized = normalize_path(
            path
        )

        document = documents.get(
            normalized
        )

        if document is None:
            document = _MutableRanks(
                path=path
            )

            documents[
                normalized
            ] = document

        if source == "vector":
            document.vector_rank = rank

        elif source == "lexical":
            document.lexical_rank = rank

        elif source == "path":
            document.path_rank = rank

        else:
            raise ValueError(
                f"Unsupported source: {source}"
            )


def _build_result(
    document: _MutableRanks,
) -> MultiSourceFusionResult:
    ranks = [
        rank
        for rank in (
            document.vector_rank,
            document.lexical_rank,
            document.path_rank,
        )
        if rank is not None
    ]

    if not ranks:
        raise ValueError(
            "Document has no source rankings"
        )

    return MultiSourceFusionResult(
        path=document.path,
        best_rank=min(ranks),
        source_count=len(ranks),
        rank_sum=sum(ranks),
        vector_rank=document.vector_rank,
        lexical_rank=document.lexical_rank,
        path_rank=document.path_rank,
    )


def best_rank_fusion(
    candidates: MultiSourceCandidates,
    *,
    final_k: int,
) -> list[MultiSourceFusionResult]:
    """
    Fusiona rankings preservando la mejor posición
    conseguida por cada documento.

    Prioridad:

    1. Mejor rank obtenido en cualquier fuente.
    2. Mayor número de fuentes que recuperan el documento.
    3. Menor suma de ranks.
    4. Ruta normalizada para desempate determinista.

    A diferencia de RRF, un documento muy fuerte en una
    única fuente no es penalizado simplemente porque no
    aparezca en las demás.
    """
    if final_k <= 0:
        raise ValueError(
            "final_k must be greater than zero"
        )

    documents: dict[
        str,
        _MutableRanks,
    ] = {}

    _register_ranking(
        documents,
        paths=candidates.vector_files,
        source="vector",
    )

    _register_ranking(
        documents,
        paths=candidates.lexical_files,
        source="lexical",
    )

    _register_ranking(
        documents,
        paths=candidates.path_files,
        source="path",
    )

    results = [
        _build_result(
            document
        )
        for document in documents.values()
    ]

    results.sort(
        key=lambda result: (
            result.best_rank,
            -result.source_count,
            result.rank_sum,
            normalize_path(
                result.path
            ),
        )
    )

    return results[:final_k]