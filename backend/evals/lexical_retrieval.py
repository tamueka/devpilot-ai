from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db.models import Chunk, Document


DEFAULT_LEXICAL_CANDIDATE_K = 20
PATH_RANK_WEIGHT = 3.0


@dataclass(frozen=True)
class LexicalSearchResult:
    path: str
    rank: float


RetrievalFunction = Callable[
    [str, int],
    Sequence[str],
]


STOP_WORDS = {
    "a",
    "al",
    "como",
    "con",
    "cual",
    "cuando",
    "de",
    "del",
    "donde",
    "el",
    "en",
    "es",
    "esta",
    "este",
    "la",
    "las",
    "lo",
    "los",
    "mas",
    "para",
    "por",
    "que",
    "se",
    "su",
    "sus",
    "un",
    "una",
    "y",
    "devpilot",
    "ai",
}


QUERY_EXPANSIONS: dict[str, tuple[str, ...]] = {
    "accede": (
        "access",
    ),
    "acceda": (
        "access",
    ),
    "acceso": (
        "access",
    ),
    "autenticacion": (
        "auth",
        "authentication",
    ),
    "autenticado": (
        "auth",
        "authenticated",
    ),
    "autenticacion": (
        "auth",
        "authentication",
    ),
    "busqueda": (
        "search",
    ),
    "conversacion": (
        "conversation",
    ),
    "embeddings": (
        "embedding",
        "embeddings",
    ),
    "estado": (
        "state",
        "store",
    ),
    "fragmentos": (
        "chunk",
        "chunks",
    ),
    "genera": (
        "generate",
        "generation",
    ),
    "generan": (
        "generate",
        "generation",
    ),
    "generar": (
        "generate",
        "generation",
    ),
    "historial": (
        "history",
        "conversation",
    ),
    "peticion": (
        "request",
        "http",
    ),
    "peticiones": (
        "request",
        "http",
    ),
    "pertenece": (
        "owner",
        "ownership",
    ),
    "pertenecen": (
        "owner",
        "ownership",
    ),
    "proyecto": (
        "project",
    ),
    "proyectos": (
        "project",
    ),
    "repositorio": (
        "repository",
        "repo",
    ),
    "semantica": (
        "semantic",
        "search",
    ),
    "servicio": (
        "service",
    ),
    "token": (
        "token",
        "jwt",
    ),
    "tokens": (
        "token",
        "jwt",
    ),
    "usuario": (
        "user",
    ),
    "usuarios": (
        "user",
    ),
    "valida": (
        "validate",
        "validation",
    ),
    "validan": (
        "validate",
        "validation",
    ),
}


def normalize_word(
    value: str,
) -> str:
    """
    Normaliza una palabra únicamente para comparaciones
    internas y expansión de términos.
    """
    normalized = unicodedata.normalize(
        "NFKD",
        value,
    )

    return "".join(
        character
        for character in normalized
        if not unicodedata.combining(
            character
        )
    ).casefold()


def extract_query_terms(
    query: str,
) -> tuple[str, ...]:
    """
    Extrae términos significativos de una pregunta y
    añade expansiones útiles para repositorios cuyo código
    está principalmente en inglés.

    No utiliza información del dataset esperado.
    """
    raw_terms = re.findall(
        r"\w+",
        query,
        flags=re.UNICODE,
    )

    terms: list[str] = []
    seen: set[str] = set()

    for raw_term in raw_terms:
        normalized = normalize_word(
            raw_term
        )

        if (
            len(normalized) < 2
            or normalized in STOP_WORDS
        ):
            continue

        candidates = [
            normalized,
            *QUERY_EXPANSIONS.get(
                normalized,
                (),
            ),
        ]

        for candidate in candidates:
            normalized_candidate = normalize_word(
                candidate
            )

            if normalized_candidate in seen:
                continue

            seen.add(
                normalized_candidate
            )

            terms.append(
                normalized_candidate
            )

    return tuple(
        terms
    )


def build_lexical_query(
    query: str,
) -> str:
    """
    Construye una consulta PostgreSQL tsquery basada
    en OR y prefix matching.

    Ejemplo:

        "búsqueda semántica"

    se convierte aproximadamente en:

        busqueda:* | search:* | semantica:* | semantic:*
    """
    terms = extract_query_terms(
        query
    )

    return " | ".join(
        f"{term}:*"
        for term in terms
    )


def search_project_documents_lexically(
    db: Session,
    project_id: UUID,
    query: str,
    top_k: int = DEFAULT_LEXICAL_CANDIDATE_K,
) -> list[LexicalSearchResult]:
    """
    Realiza Full-Text Search sobre:

    - path normalizado del documento
    - contenido de sus chunks

    El path recibe mayor peso para favorecer nombres
    relevantes como:

        semantic_search_service.py
        resource_access.py
        auth.store.ts
    """
    if top_k <= 0:
        raise ValueError(
            "top_k must be greater than zero"
        )

    lexical_query = build_lexical_query(
        query
    )

    if not lexical_query:
        return []

    normalized_path = func.regexp_replace(
        Document.path,
        r"[/_.-]+",
        " ",
        "g",
    )

    path_vector = func.to_tsvector(
        "simple",
        func.coalesce(
            normalized_path,
            "",
        ),
    )

    content_vector = func.to_tsvector(
        "simple",
        func.coalesce(
            Chunk.content,
            "",
        ),
    )

    search_query = func.to_tsquery(
        "simple",
        lexical_query,
    )

    path_rank = func.ts_rank_cd(
        path_vector,
        search_query,
    )

    content_rank = func.ts_rank_cd(
        content_vector,
        search_query,
    )

    combined_rank = (
        path_rank * PATH_RANK_WEIGHT
        + content_rank
    )

    best_rank = func.max(
        combined_rank
    ).label(
        "rank"
    )

    statement = (
        select(
            Document.path,
            best_rank,
        )
        .join(
            Chunk,
            Chunk.document_id
            == Document.id,
        )
        .where(
            Document.project_id
            == project_id,
            or_(
                path_vector.op("@@")(
                    search_query
                ),
                content_vector.op("@@")(
                    search_query
                ),
            ),
        )
        .group_by(
            Document.path,
        )
        .order_by(
            best_rank.desc(),
            Document.path.asc(),
        )
        .limit(
            top_k
        )
    )

    rows = db.execute(
        statement
    ).all()

    return [
        LexicalSearchResult(
            path=path,
            rank=float(rank),
        )
        for path, rank in rows
    ]


def build_lexical_retriever(
    db: Session,
    project_id: UUID,
    *,
    candidate_k: int = DEFAULT_LEXICAL_CANDIDATE_K,
) -> RetrievalFunction:
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

        results = (
            search_project_documents_lexically(
                db=db,
                project_id=project_id,
                query=question,
                top_k=search_top_k,
            )
        )

        return [
            result.path
            for result in results[:k]
        ]

    return retrieve