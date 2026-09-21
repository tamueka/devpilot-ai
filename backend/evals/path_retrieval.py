from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Chunk, Document
from evals.lexical_retrieval import (
    extract_query_terms,
    normalize_word,
)


DEFAULT_PATH_CANDIDATE_K = 20

FILENAME_EXACT_WEIGHT = 8.0
FILENAME_PREFIX_WEIGHT = 5.0

PATH_EXACT_WEIGHT = 3.0
PATH_PREFIX_WEIGHT = 1.5

SOURCE_DIRECTORY_BONUS = 3.0
DOCUMENTATION_DIRECTORY_PENALTY = 1.0
TEST_DIRECTORY_PENALTY = 3.0


@dataclass(frozen=True)
class PathSearchResult:
    path: str
    score: float


RetrievalFunction = Callable[
    [str, int],
    Sequence[str],
]


PATH_QUERY_EXPANSIONS: dict[
    str,
    tuple[str, ...],
] = {
    "adaptador": (
        "adapter",
        "adapters",
    ),
    "adaptadores": (
        "adapter",
        "adapters",
    ),
    "argumento": (
        "argument",
        "arguments",
    ),
    "argumentos": (
        "argument",
        "arguments",
    ),
    "autocompletado": (
        "completion",
        "autocomplete",
    ),
    "cabecera": (
        "header",
        "headers",
    ),
    "cabeceras": (
        "header",
        "headers",
    ),
    "completado": (
        "completion",
    ),
    "configuracion": (
        "config",
        "configuration",
        "options",
    ),
    "cuerpo": (
        "body",
    ),
    "cuerpos": (
        "body",
    ),
    "decorador": (
        "decorator",
        "decorators",
    ),
    "decoradores": (
        "decorator",
        "decorators",
    ),
    "error": (
        "error",
        "errors",
    ),
    "errores": (
        "error",
        "errors",
    ),
    "formatea": (
        "format",
        "formatting",
    ),
    "formatear": (
        "format",
        "formatting",
    ),
    "formateo": (
        "format",
        "formatting",
    ),
    "formato": (
        "format",
        "formatting",
    ),
    "formatos": (
        "format",
        "formatting",
    ),
    "gancho": (
        "hook",
        "hooks",
    ),
    "ganchos": (
        "hook",
        "hooks",
    ),
    "incremento": (
        "increment",
        "bump",
    ),
    "incrementos": (
        "increment",
        "bump",
    ),
    "interfaz": (
        "ui",
    ),
    "normaliza": (
        "normalize",
        "normalization",
    ),
    "normalizacion": (
        "normalize",
        "normalization",
    ),
    "normalizar": (
        "normalize",
        "normalization",
    ),
    "opcion": (
        "option",
        "options",
    ),
    "opciones": (
        "option",
        "options",
    ),
    "parametro": (
        "parameter",
        "parameters",
        "param",
    ),
    "parametros": (
        "parameter",
        "parameters",
        "param",
    ),
    "prueba": (
        "test",
        "testing",
    ),
    "pruebas": (
        "test",
        "testing",
    ),
    "probar": (
        "test",
        "testing",
    ),
    "reintento": (
        "retry",
        "retries",
    ),
    "reintentos": (
        "retry",
        "retries",
    ),
    "respuesta": (
        "response",
    ),
    "respuestas": (
        "response",
    ),
    "red": (
        "network",
    ),
    "suscripcion": (
        "subscription",
        "subscriptions",
    ),
    "suscripciones": (
        "subscription",
        "subscriptions",
    ),
    "terminal": (
        "terminal",
        "term",
        "termui",
    ),
    "tiempo": (
        "time",
        "timeout",
    ),
    "utilidad": (
        "util",
        "utils",
        "utility",
        "utilities",
    ),
    "utilidades": (
        "util",
        "utils",
        "utility",
        "utilities",
    ),
}


IMPLEMENTATION_QUERY_TERMS = {
    "archivo",
    "contiene",
    "define",
    "implementa",
    "implementacion",
    "logica",
    "proporciona",
    "servicio",
}


SOURCE_DIRECTORY_TOKENS = {
    "app",
    "lib",
    "libs",
    "package",
    "packages",
    "source",
    "src",
}


DOCUMENTATION_DIRECTORY_TOKENS = {
    "doc",
    "docs",
    "documentation",
}


TEST_DIRECTORY_TOKENS = {
    "spec",
    "specs",
    "test",
    "tests",
}


def split_identifier(
    value: str,
) -> tuple[str, ...]:
    """
    Divide nombres de fichero y segmentos de ruta.

    Ejemplos:

        ResponsePromise
        -> response, promise

        retry-timing
        -> retry, timing

        semantic_search_service
        -> semantic, search, service
    """
    value = re.sub(
        r"([a-z0-9])([A-Z])",
        r"\1 \2",
        value,
    )

    value = re.sub(
        r"([A-Z]+)([A-Z][a-z])",
        r"\1 \2",
        value,
    )

    raw_tokens = re.findall(
        r"[A-Za-z0-9]+",
        value,
    )

    result: list[str] = []

    for token in raw_tokens:
        normalized = normalize_word(
            token
        )

        if not normalized:
            continue

        result.append(
            normalized
        )

    return tuple(
        result
    )


def tokenize_path(
    path: str,
) -> tuple[str, ...]:
    """
    Convierte una ruta completa en tokens comparables.
    """
    normalized_path = path.replace(
        "\\",
        "/",
    )

    segments = normalized_path.split(
        "/"
    )

    tokens: list[str] = []

    for segment in segments:
        tokens.extend(
            split_identifier(
                segment
            )
        )

    return tuple(
        tokens
    )


def filename_tokens(
    path: str,
) -> tuple[str, ...]:
    """
    Extrae tokens únicamente del nombre del fichero.
    """
    normalized_path = path.replace(
        "\\",
        "/",
    )

    filename = normalized_path.rsplit(
        "/",
        maxsplit=1,
    )[-1]

    return split_identifier(
        filename
    )


def directory_tokens(
    path: str,
) -> tuple[str, ...]:
    """
    Extrae únicamente los tokens correspondientes
    a directorios.
    """
    normalized_path = path.replace(
        "\\",
        "/",
    )

    parts = normalized_path.split(
        "/"
    )

    if len(parts) <= 1:
        return ()

    tokens: list[str] = []

    for part in parts[:-1]:
        tokens.extend(
            split_identifier(
                part
            )
        )

    return tuple(
        tokens
    )


def raw_query_terms(
    query: str,
) -> tuple[str, ...]:
    raw_terms = re.findall(
        r"\w+",
        query,
        flags=re.UNICODE,
    )

    return tuple(
        normalize_word(term)
        for term in raw_terms
        if normalize_word(term)
    )


def extract_path_query_terms(
    query: str,
) -> tuple[str, ...]:
    """
    Reutiliza las expansiones lexicales existentes y
    añade vocabulario específico de navegación por código.

    Las expansiones son genéricas y no contienen nombres
    de archivos del dataset.
    """
    terms: list[str] = []
    seen: set[str] = set()

    def add_term(
        value: str,
    ) -> None:
        normalized = normalize_word(
            value
        )

        if (
            not normalized
            or normalized in seen
        ):
            return

        seen.add(
            normalized
        )

        terms.append(
            normalized
        )

    for term in extract_query_terms(
        query
    ):
        add_term(
            term
        )

    for raw_term in raw_query_terms(
        query
    ):
        for expansion in (
            PATH_QUERY_EXPANSIONS.get(
                raw_term,
                (),
            )
        ):
            add_term(
                expansion
            )

    return tuple(
        terms
    )


def token_prefix_match(
    left: str,
    right: str,
) -> bool:
    """
    Permite coincidencias como:

        util    <-> utils
        format  <-> formatting
        decorator <-> decorators

    Se exige una longitud mínima para evitar
    coincidencias demasiado genéricas.
    """
    if (
        len(left) < 3
        or len(right) < 3
    ):
        return False

    return (
        left.startswith(right)
        or right.startswith(left)
    )


def best_token_score(
    query_term: str,
    candidate_tokens: tuple[str, ...],
    *,
    exact_weight: float,
    prefix_weight: float,
) -> float:
    if query_term in candidate_tokens:
        return exact_weight

    if any(
        token_prefix_match(
            query_term,
            candidate,
        )
        for candidate in candidate_tokens
    ):
        return prefix_weight

    return 0.0


def has_implementation_intent(
    query: str,
) -> bool:
    terms = set(
        raw_query_terms(
            query
        )
    )

    return bool(
        terms.intersection(
            IMPLEMENTATION_QUERY_TERMS
        )
    )


def score_document_path(
    path: str,
    query: str,
) -> float:
    """
    Calcula un score exclusivamente a partir de:

    - nombre del fichero
    - ruta
    - estructura típica de repositorios

    No utiliza contenido de chunks.
    """
    query_terms = (
        extract_path_query_terms(
            query
        )
    )

    if not query_terms:
        return 0.0

    file_tokens = filename_tokens(
        path
    )

    all_path_tokens = tokenize_path(
        path
    )

    directories = set(
        directory_tokens(
            path
        )
    )

    score = 0.0

    for query_term in query_terms:
        score += best_token_score(
            query_term,
            file_tokens,
            exact_weight=(
                FILENAME_EXACT_WEIGHT
            ),
            prefix_weight=(
                FILENAME_PREFIX_WEIGHT
            ),
        )

        score += best_token_score(
            query_term,
            all_path_tokens,
            exact_weight=(
                PATH_EXACT_WEIGHT
            ),
            prefix_weight=(
                PATH_PREFIX_WEIGHT
            ),
        )

    if has_implementation_intent(
        query
    ):
        if directories.intersection(
            SOURCE_DIRECTORY_TOKENS
        ):
            score += (
                SOURCE_DIRECTORY_BONUS
            )

        if directories.intersection(
            DOCUMENTATION_DIRECTORY_TOKENS
        ):
            score -= (
                DOCUMENTATION_DIRECTORY_PENALTY
            )

        if directories.intersection(
            TEST_DIRECTORY_TOKENS
        ):
            score -= (
                TEST_DIRECTORY_PENALTY
            )

    return max(
        score,
        0.0,
    )


def search_project_documents_by_path(
    db: Session,
    project_id: UUID,
    query: str,
    top_k: int = DEFAULT_PATH_CANDIDATE_K,
) -> list[PathSearchResult]:
    """
    Recupera documentos únicamente mediante señales
    procedentes de su ruta.

    Se limita a documentos que tengan al menos un Chunk
    para garantizar que puedan participar después en RAG
    o reranking.
    """
    if top_k <= 0:
        raise ValueError(
            "top_k must be greater than zero"
        )

    statement = (
        select(
            Document.path
        )
        .join(
            Chunk,
            Chunk.document_id
            == Document.id,
        )
        .where(
            Document.project_id
            == project_id
        )
        .group_by(
            Document.path
        )
        .order_by(
            Document.path.asc()
        )
    )

    paths = list(
        db.scalars(
            statement
        ).all()
    )

    scored_results = [
        PathSearchResult(
            path=path,
            score=score_document_path(
                path=path,
                query=query,
            ),
        )
        for path in paths
    ]

    positive_results = [
        result
        for result in scored_results
        if result.score > 0
    ]

    positive_results.sort(
        key=lambda result: (
            -result.score,
            result.path,
        )
    )

    return positive_results[
        :top_k
    ]


def build_path_retriever(
    db: Session,
    project_id: UUID,
    *,
    candidate_k: int = DEFAULT_PATH_CANDIDATE_K,
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
            search_project_documents_by_path(
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