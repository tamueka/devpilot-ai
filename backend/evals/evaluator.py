from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from evals.retrieval_metrics import (
    code_ratio_at_k,
    documentation_ratio_at_k,
    hit_at_k,
    mean_metric,
    recall_at_k,
    reciprocal_rank,
    unique_documents_at_k,
)


DEFAULT_DATASET_PATH = (
    Path(__file__).parent
    / "datasets"
    / "rag_eval.json"
)


RetrievalFunction = Callable[
    [str, int],
    Sequence[str],
]


@dataclass(frozen=True)
class EvaluationCase:
    id: str
    category: str
    question: str
    expected_files: tuple[str, ...]


@dataclass(frozen=True)
class CaseEvaluationResult:
    case_id: str
    category: str
    question: str
    expected_files: tuple[str, ...]
    retrieved_files: tuple[str, ...]

    hit_at_1: float
    hit_at_3: float
    hit_at_5: float
    recall_at_5: float
    reciprocal_rank: float

    unique_documents_at_5: int
    documentation_ratio_at_5: float
    code_ratio_at_5: float

    latency_ms: float


@dataclass(frozen=True)
class EvaluationSummary:
    total_cases: int

    hit_at_1: float
    hit_at_3: float
    hit_at_5: float
    recall_at_5: float
    mrr: float

    average_unique_documents_at_5: float
    average_documentation_ratio_at_5: float
    average_code_ratio_at_5: float

    average_latency_ms: float


@dataclass(frozen=True)
class EvaluationReport:
    dataset_name: str
    dataset_version: str
    results: list[CaseEvaluationResult]
    summary: EvaluationSummary


def load_dataset(
    dataset_path: str | Path | None = None,
) -> tuple[
    str,
    str,
    list[EvaluationCase],
]:
    """
    Carga un dataset de evaluación RAG.

    Si dataset_path es None, utiliza el dataset principal:

        evals/datasets/rag_eval.json

    También permite cargar datasets alternativos para poder
    separar development/tuning y evaluación held-out.
    """
    path = (
        Path(dataset_path)
        if dataset_path is not None
        else DEFAULT_DATASET_PATH
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Evaluation dataset not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        raw_dataset = json.load(
            file
        )

    if not isinstance(
        raw_dataset,
        dict,
    ):
        raise ValueError(
            "Evaluation dataset must be a JSON object"
        )

    metadata = raw_dataset.get(
        "metadata"
    )

    if not isinstance(
        metadata,
        dict,
    ):
        raise ValueError(
            "Evaluation dataset must contain metadata"
        )

    dataset_name = metadata.get(
        "name"
    )

    dataset_version = metadata.get(
        "version"
    )

    if (
        not isinstance(
            dataset_name,
            str,
        )
        or not dataset_name.strip()
    ):
        raise ValueError(
            "Evaluation dataset metadata.name "
            "must be a non-empty string"
        )

    if (
        not isinstance(
            dataset_version,
            str,
        )
        or not dataset_version.strip()
    ):
        raise ValueError(
            "Evaluation dataset metadata.version "
            "must be a non-empty string"
        )

    raw_cases = raw_dataset.get(
        "cases"
    )

    if not isinstance(
        raw_cases,
        list,
    ):
        raise ValueError(
            "Evaluation dataset cases must be a list"
        )

    cases: list[EvaluationCase] = []

    for index, raw_case in enumerate(
        raw_cases,
        start=1,
    ):
        if not isinstance(
            raw_case,
            dict,
        ):
            raise ValueError(
                "Evaluation case "
                f"{index} must be a JSON object"
            )

        case_id = raw_case.get(
            "id"
        )

        category = raw_case.get(
            "category"
        )

        question = raw_case.get(
            "question"
        )

        expected_files = raw_case.get(
            "expected_files"
        )

        if (
            not isinstance(
                case_id,
                str,
            )
            or not case_id.strip()
        ):
            raise ValueError(
                "Evaluation case "
                f"{index} has an invalid id"
            )

        if (
            not isinstance(
                category,
                str,
            )
            or not category.strip()
        ):
            raise ValueError(
                "Evaluation case "
                f"{case_id} has an invalid category"
            )

        if (
            not isinstance(
                question,
                str,
            )
            or not question.strip()
        ):
            raise ValueError(
                "Evaluation case "
                f"{case_id} has an invalid question"
            )

        if (
            not isinstance(
                expected_files,
                list,
            )
            or not expected_files
            or not all(
                isinstance(
                    path,
                    str,
                )
                and path.strip()
                for path in expected_files
            )
        ):
            raise ValueError(
                "Evaluation case "
                f"{case_id} must contain at least "
                "one expected file"
            )

        cases.append(
            EvaluationCase(
                id=case_id,
                category=category,
                question=question,
                expected_files=tuple(
                    expected_files
                ),
            )
        )

    return (
        dataset_name,
        dataset_version,
        cases,
    )


def evaluate_case(
    case: EvaluationCase,
    retrieve: RetrievalFunction,
    *,
    retrieval_k: int = 5,
) -> CaseEvaluationResult:
    """
    Evalúa un único caso contra una estrategia de retrieval.

    retrieval_k debe ser >= 5 porque el benchmark calcula
    métricas Hit@1, Hit@3, Hit@5 y Recall@5.
    """
    if retrieval_k < 5:
        raise ValueError(
            "retrieval_k must be greater than or equal to 5"
        )

    started_at = perf_counter()

    retrieved_files = list(
        retrieve(
            case.question,
            retrieval_k,
        )
    )

    latency_ms = (
        perf_counter()
        - started_at
    ) * 1000.0

    return CaseEvaluationResult(
        case_id=case.id,
        category=case.category,
        question=case.question,
        expected_files=case.expected_files,
        retrieved_files=tuple(
            retrieved_files
        ),
        hit_at_1=hit_at_k(
            retrieved_files,
            case.expected_files,
            1,
        ),
        hit_at_3=hit_at_k(
            retrieved_files,
            case.expected_files,
            3,
        ),
        hit_at_5=hit_at_k(
            retrieved_files,
            case.expected_files,
            5,
        ),
        recall_at_5=recall_at_k(
            retrieved_files,
            case.expected_files,
            5,
        ),
        reciprocal_rank=reciprocal_rank(
            retrieved_files,
            case.expected_files,
        ),
        unique_documents_at_5=(
            unique_documents_at_k(
                retrieved_files,
                5,
            )
        ),
        documentation_ratio_at_5=(
            documentation_ratio_at_k(
                retrieved_files,
                5,
            )
        ),
        code_ratio_at_5=(
            code_ratio_at_k(
                retrieved_files,
                5,
            )
        ),
        latency_ms=latency_ms,
    )


def build_summary(
    results: Sequence[CaseEvaluationResult],
) -> EvaluationSummary:
    """
    Construye las métricas agregadas del benchmark.
    """
    if not results:
        return EvaluationSummary(
            total_cases=0,
            hit_at_1=0.0,
            hit_at_3=0.0,
            hit_at_5=0.0,
            recall_at_5=0.0,
            mrr=0.0,
            average_unique_documents_at_5=0.0,
            average_documentation_ratio_at_5=0.0,
            average_code_ratio_at_5=0.0,
            average_latency_ms=0.0,
        )

    return EvaluationSummary(
        total_cases=len(
            results
        ),
        hit_at_1=mean_metric(
            [
                result.hit_at_1
                for result in results
            ]
        ),
        hit_at_3=mean_metric(
            [
                result.hit_at_3
                for result in results
            ]
        ),
        hit_at_5=mean_metric(
            [
                result.hit_at_5
                for result in results
            ]
        ),
        recall_at_5=mean_metric(
            [
                result.recall_at_5
                for result in results
            ]
        ),
        mrr=mean_metric(
            [
                result.reciprocal_rank
                for result in results
            ]
        ),
        average_unique_documents_at_5=(
            mean_metric(
                [
                    float(
                        result.unique_documents_at_5
                    )
                    for result in results
                ]
            )
        ),
        average_documentation_ratio_at_5=(
            mean_metric(
                [
                    result.documentation_ratio_at_5
                    for result in results
                ]
            )
        ),
        average_code_ratio_at_5=(
            mean_metric(
                [
                    result.code_ratio_at_5
                    for result in results
                ]
            )
        ),
        average_latency_ms=mean_metric(
            [
                result.latency_ms
                for result in results
            ]
        ),
    )


def evaluate_dataset(
    retrieve: RetrievalFunction,
    *,
    retrieval_k: int = 5,
    dataset_path: str | Path | None = None,
) -> EvaluationReport:
    """
    Ejecuta una estrategia de retrieval sobre un dataset completo.

    dataset_path permite utilizar datasets independientes sin
    modificar el dataset de desarrollo.
    """
    if retrieval_k < 5:
        raise ValueError(
            "retrieval_k must be greater than or equal to 5"
        )

    (
        dataset_name,
        dataset_version,
        cases,
    ) = load_dataset(
        dataset_path=dataset_path,
    )

    results = [
        evaluate_case(
            case=case,
            retrieve=retrieve,
            retrieval_k=retrieval_k,
        )
        for case in cases
    ]

    return EvaluationReport(
        dataset_name=dataset_name,
        dataset_version=dataset_version,
        results=results,
        summary=build_summary(
            results
        ),
    )