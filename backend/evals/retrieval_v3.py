from __future__ import annotations

from collections.abc import Callable, Sequence
from uuid import UUID

from openai import OpenAI
from sqlalchemy.orm import Session

from evals.llm_reranker import (
    DEFAULT_MAX_CHARS_PER_DOCUMENT,
    DEFAULT_RERANK_MODEL,
)
from evals.retrieval_v2 import (
    build_retrieval_v2_retriever,
)


DEFAULT_RETRIEVAL_V3_CANDIDATE_K = 20


RetrievalFunction = Callable[
    [str, int],
    Sequence[str],
]


def build_retrieval_v3_retriever(
    *,
    db: Session,
    project_id: UUID,
    candidate_k: int = (
        DEFAULT_RETRIEVAL_V3_CANDIDATE_K
    ),
    model: str = DEFAULT_RERANK_MODEL,
    max_chars_per_document: int = (
        DEFAULT_MAX_CHARS_PER_DOCUMENT
    ),
    client: OpenAI | None = None,
) -> RetrievalFunction:
    """
    Construye Retrieval v3.

    Retrieval v3 mantiene el pipeline estable de v2:

        Vector@20
            +
        Lexical@20
            +
        Path@20
            ↓
        Best-Rank fusion
            ↓
        candidate_k
            ↓
        LLM reranker
            ↓
        Top K

    Cambios respecto a la configuración original de v2:

    - Path Retrieval incorpora las expansiones genéricas
      desarrolladas durante Retrieval v3.
    - El conjunto enviado al reranker aumenta de 10 a 20
      candidatos.

    Best-Rank se mantiene como estrategia de fusión hasta
    disponer de evidencia de tres fuentes que justifique
    sustituirlo.
    """
    return build_retrieval_v2_retriever(
        db=db,
        project_id=project_id,
        candidate_k=candidate_k,
        model=model,
        max_chars_per_document=(
            max_chars_per_document
        ),
        client=client,
    )