from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from evals.lexical_retrieval import (
    DEFAULT_LEXICAL_CANDIDATE_K,
    build_lexical_retriever,
)
from evals.path_retrieval import (
    DEFAULT_PATH_CANDIDATE_K,
    build_path_retriever,
)
from evals.retrieval_metrics import normalize_path
from evals.vector_candidate_retrieval import (
    DEFAULT_CHUNK_CANDIDATE_K,
    build_vector_candidate_retriever,
)


DEFAULT_VECTOR_DOCUMENT_K = 20
DEFAULT_LEXICAL_DOCUMENT_K = 20
DEFAULT_PATH_DOCUMENT_K = 20


@dataclass(frozen=True)
class MultiSourceCandidates:
    vector_files: tuple[str, ...]
    lexical_files: tuple[str, ...]
    path_files: tuple[str, ...]
    union_files: tuple[str, ...]


CandidateCollector = Callable[
    [str],
    MultiSourceCandidates,
]


def merge_unique_paths(
    *path_groups: tuple[str, ...],
) -> tuple[str, ...]:
    """
    Combina varias listas de rutas eliminando duplicados.

    Se conserva el orden de aparición:

        vector
        -> lexical
        -> path

    Este orden NO representa todavía un ranking final.
    La unión se utiliza únicamente como candidate pool.
    """
    merged: list[str] = []
    seen: set[str] = set()

    for paths in path_groups:
        for path in paths:
            normalized = normalize_path(
                path
            )

            if normalized in seen:
                continue

            seen.add(
                normalized
            )

            merged.append(
                path
            )

    return tuple(
        merged
    )


def build_multi_source_candidate_collector(
    db: Session,
    project_id: UUID,
    *,
    vector_document_k: int = (
        DEFAULT_VECTOR_DOCUMENT_K
    ),
    lexical_document_k: int = (
        DEFAULT_LEXICAL_DOCUMENT_K
    ),
    path_document_k: int = (
        DEFAULT_PATH_DOCUMENT_K
    ),
    chunk_candidate_k: int = (
        DEFAULT_CHUNK_CANDIDATE_K
    ),
) -> CandidateCollector:
    """
    Construye un collector de candidatos procedentes de:

    - búsqueda vectorial
    - búsqueda lexical
    - búsqueda basada en rutas

    No realiza ninguna fusión de scores ni ranking final.

    Su responsabilidad es únicamente generar y conservar
    el candidate pool de las tres fuentes.
    """
    if vector_document_k <= 0:
        raise ValueError(
            "vector_document_k must be greater than zero"
        )

    if lexical_document_k <= 0:
        raise ValueError(
            "lexical_document_k must be greater than zero"
        )

    if path_document_k <= 0:
        raise ValueError(
            "path_document_k must be greater than zero"
        )

    if chunk_candidate_k <= 0:
        raise ValueError(
            "chunk_candidate_k must be greater than zero"
        )

    vector_retrieve = (
        build_vector_candidate_retriever(
            db=db,
            project_id=project_id,
            chunk_candidate_k=(
                chunk_candidate_k
            ),
        )
    )

    lexical_retrieve = (
        build_lexical_retriever(
            db=db,
            project_id=project_id,
            candidate_k=(
                lexical_document_k
            ),
        )
    )

    path_retrieve = (
        build_path_retriever(
            db=db,
            project_id=project_id,
            candidate_k=(
                path_document_k
            ),
        )
    )

    def collect(
        question: str,
    ) -> MultiSourceCandidates:
        if not question.strip():
            raise ValueError(
                "question must not be blank"
            )

        vector_files = tuple(
            vector_retrieve(
                question,
                vector_document_k,
            )
        )

        lexical_files = tuple(
            lexical_retrieve(
                question,
                lexical_document_k,
            )
        )

        path_files = tuple(
            path_retrieve(
                question,
                path_document_k,
            )
        )

        union_files = merge_unique_paths(
            vector_files,
            lexical_files,
            path_files,
        )

        return MultiSourceCandidates(
            vector_files=vector_files,
            lexical_files=lexical_files,
            path_files=path_files,
            union_files=union_files,
        )

    return collect
