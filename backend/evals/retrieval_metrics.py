from __future__ import annotations

from collections.abc import Iterable, Sequence


def normalize_path(path: str) -> str:
    """
    Normaliza una ruta para poder comparar resultados procedentes de
    diferentes sistemas operativos.

    Ejemplos:
        backend\\app\\services\\rag_service.py
        backend/app/services/rag_service.py

    Ambas rutas se consideran equivalentes.
    """
    normalized = path.strip().replace("\\", "/")

    while normalized.startswith("./"):
        normalized = normalized[2:]

    return normalized.casefold()


def hit_at_k(
    retrieved_files: Sequence[str],
    expected_files: Iterable[str],
    k: int,
) -> float:
    """
    Devuelve 1.0 si al menos uno de los archivos esperados aparece
    entre los primeros K resultados recuperados.

    Devuelve 0.0 en caso contrario.
    """
    if k <= 0:
        raise ValueError("k must be greater than zero")

    expected = {normalize_path(path) for path in expected_files}

    if not expected:
        return 0.0

    retrieved = {
        normalize_path(path)
        for path in retrieved_files[:k]
    }

    return 1.0 if expected.intersection(retrieved) else 0.0


def reciprocal_rank(
    retrieved_files: Sequence[str],
    expected_files: Iterable[str],
) -> float:
    """
    Calcula Reciprocal Rank.

    Si el primer resultado relevante aparece en posición:

        1 -> 1.0
        2 -> 0.5
        3 -> 0.333...
        4 -> 0.25

    Si ningún resultado es relevante, devuelve 0.0.
    """
    expected = {normalize_path(path) for path in expected_files}

    if not expected:
        return 0.0

    for index, retrieved_file in enumerate(retrieved_files, start=1):
        if normalize_path(retrieved_file) in expected:
            return 1.0 / index

    return 0.0


def recall_at_k(
    retrieved_files: Sequence[str],
    expected_files: Iterable[str],
    k: int,
) -> float:
    """
    Calcula qué proporción de los archivos esperados aparece
    entre los primeros K resultados.

    Es especialmente útil para casos donde una pregunta tiene
    más de un archivo relevante.
    """
    if k <= 0:
        raise ValueError("k must be greater than zero")

    expected = {normalize_path(path) for path in expected_files}

    if not expected:
        return 0.0

    retrieved = {
        normalize_path(path)
        for path in retrieved_files[:k]
    }

    relevant_retrieved = expected.intersection(retrieved)

    return len(relevant_retrieved) / len(expected)


def mean_reciprocal_rank(
    reciprocal_ranks: Iterable[float],
) -> float:
    """
    Calcula Mean Reciprocal Rank (MRR) para un conjunto de casos.
    """
    values = list(reciprocal_ranks)

    if not values:
        return 0.0

    return sum(values) / len(values)


def mean_metric(values: Iterable[float]) -> float:
    """
    Calcula la media de una métrica.

    Se utilizará para obtener, por ejemplo:

        Hit@1 medio
        Hit@3 medio
        Hit@5 medio
        Recall@5 medio
    """
    metric_values = list(values)

    if not metric_values:
        return 0.0

    return sum(metric_values) / len(metric_values)

def unique_documents_at_k(
    retrieved_files: Sequence[str],
    k: int,
) -> int:
    """
    Devuelve el número de documentos únicos presentes
    entre los primeros K resultados.

    Como el retrieval trabaja con chunks, un mismo documento
    puede aparecer varias veces.
    """
    if k <= 0:
        raise ValueError("k must be greater than zero")

    return len(
        {
            normalize_path(path)
            for path in retrieved_files[:k]
        }
    )


def documentation_ratio_at_k(
    retrieved_files: Sequence[str],
    k: int,
) -> float:
    """
    Calcula qué proporción de los primeros K resultados
    corresponde a documentación Markdown.
    """
    if k <= 0:
        raise ValueError("k must be greater than zero")

    top_k = retrieved_files[:k]

    if not top_k:
        return 0.0

    documentation_results = sum(
        1
        for path in top_k
        if normalize_path(path).endswith(".md")
    )

    return documentation_results / len(top_k)


def code_ratio_at_k(
    retrieved_files: Sequence[str],
    k: int,
) -> float:
    """
    Calcula qué proporción de los primeros K resultados
    corresponde a archivos no Markdown.

    En el contexto del benchmark de DevPilot se utiliza como
    aproximación al ratio de código frente a documentación.
    """
    if k <= 0:
        raise ValueError("k must be greater than zero")

    top_k = retrieved_files[:k]

    if not top_k:
        return 0.0

    return 1.0 - documentation_ratio_at_k(
        retrieved_files,
        k,
    )