from __future__ import annotations

import json
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from app.db.database import SessionLocal
from evals.evaluator import (
    CaseEvaluationResult,
    evaluate_dataset,
)
from evals.llm_reranker import (
    DEFAULT_MAX_CHARS_PER_DOCUMENT,
    DEFAULT_RERANK_MODEL,
)
from evals.retrieval_v2 import (
    build_retrieval_v2_retriever,
)


if hasattr(
    sys.stdout,
    "reconfigure",
):
    sys.stdout.reconfigure(
        encoding="utf-8",
    )


BACKEND_ROOT = Path(
    __file__
).resolve().parents[1]

SUITE_PATH = (
    BACKEND_ROOT
    / "evals"
    / "datasets"
    / "independent_validation_suite.json"
)

PROJECTS_PATH = (
    BACKEND_ROOT
    / "evals"
    / "datasets"
    / "independent_validation_projects.local.json"
)


FINAL_K = 5

CANDIDATE_K_VALUES = (
    10,
    15,
    20,
)


@dataclass(frozen=True)
class RepositoryRun:
    repository: str
    candidate_k: int
    results: tuple[
        CaseEvaluationResult,
        ...
    ]


@dataclass(frozen=True)
class GlobalMetrics:
    candidate_k: int
    cases: int

    hit_at_1: float
    hit_at_3: float
    hit_at_5: float
    recall_at_5: float
    mrr: float

    unique_documents_at_5: float
    documentation_ratio_at_5: float
    code_ratio_at_5: float

    average_latency_ms: float


def load_json(
    path: Path,
) -> dict:
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        payload = json.load(
            file
        )

    if not isinstance(
        payload,
        dict,
    ):
        raise ValueError(
            f"Expected JSON object: {path}"
        )

    return payload


def mean(
    values: list[float],
) -> float:
    if not values:
        return 0.0

    return statistics.fmean(
        values
    )


def calculate_metrics(
    *,
    candidate_k: int,
    results: list[
        CaseEvaluationResult
    ],
) -> GlobalMetrics:
    return GlobalMetrics(
        candidate_k=candidate_k,
        cases=len(results),
        hit_at_1=mean(
            [
                float(result.hit_at_1)
                for result in results
            ]
        ),
        hit_at_3=mean(
            [
                float(result.hit_at_3)
                for result in results
            ]
        ),
        hit_at_5=mean(
            [
                float(result.hit_at_5)
                for result in results
            ]
        ),
        recall_at_5=mean(
            [
                result.recall_at_5
                for result in results
            ]
        ),
        mrr=mean(
            [
                result.reciprocal_rank
                for result in results
            ]
        ),
        unique_documents_at_5=mean(
            [
                float(
                    result.unique_documents_at_5
                )
                for result in results
            ]
        ),
        documentation_ratio_at_5=mean(
            [
                result.documentation_ratio_at_5
                for result in results
            ]
        ),
        code_ratio_at_5=mean(
            [
                result.code_ratio_at_5
                for result in results
            ]
        ),
        average_latency_ms=mean(
            [
                result.latency_ms
                for result in results
            ]
        ),
    )


def percent(
    value: float,
) -> str:
    return f"{value * 100:.2f}%"


def print_repository_result(
    *,
    repository: str,
    candidate_k: int,
    results: tuple[
        CaseEvaluationResult,
        ...
    ],
) -> None:
    metrics = calculate_metrics(
        candidate_k=candidate_k,
        results=list(
            results
        ),
    )

    print()
    print("-" * 100)

    print(
        f"{repository} | "
        f"candidate_k={candidate_k}"
    )

    print("-" * 100)

    print(
        f"Cases:      {metrics.cases}"
    )

    print(
        f"Hit@1:      "
        f"{percent(metrics.hit_at_1)}"
    )

    print(
        f"Hit@3:      "
        f"{percent(metrics.hit_at_3)}"
    )

    print(
        f"Hit@5:      "
        f"{percent(metrics.hit_at_5)}"
    )

    print(
        f"Recall@5:   "
        f"{percent(metrics.recall_at_5)}"
    )

    print(
        f"MRR:        "
        f"{metrics.mrr:.3f}"
    )

    print(
        f"Latency:    "
        f"{metrics.average_latency_ms:.2f} ms"
    )


def print_global_metrics(
    metrics: GlobalMetrics,
) -> None:
    print()
    print("=" * 100)

    print(
        f"GLOBAL | candidate_k="
        f"{metrics.candidate_k}"
    )

    print("=" * 100)

    print(
        f"Cases:                         "
        f"{metrics.cases}"
    )

    print(
        f"Hit@1:                         "
        f"{percent(metrics.hit_at_1)}"
    )

    print(
        f"Hit@3:                         "
        f"{percent(metrics.hit_at_3)}"
    )

    print(
        f"Hit@5:                         "
        f"{percent(metrics.hit_at_5)}"
    )

    print(
        f"Recall@5:                      "
        f"{percent(metrics.recall_at_5)}"
    )

    print(
        f"MRR:                           "
        f"{metrics.mrr:.3f}"
    )

    print(
        f"Unique docs@5:                 "
        f"{metrics.unique_documents_at_5:.2f}"
    )

    print(
        f"Documentation ratio:           "
        f"{percent(metrics.documentation_ratio_at_5)}"
    )

    print(
        f"Code ratio:                    "
        f"{percent(metrics.code_ratio_at_5)}"
    )

    print(
        f"Avg pipeline latency:          "
        f"{metrics.average_latency_ms:.2f} ms"
    )


def print_comparison(
    metrics_by_k: dict[
        int,
        GlobalMetrics,
    ],
) -> None:
    print()
    print()
    print("=" * 118)

    print(
        "DEVPILOT AI - "
        "RETRIEVAL V3 CUTOFF EXPERIMENT"
    )

    print("=" * 118)

    print()
    print(
        "Development experiment."
    )

    print(
        "The former independent validation "
        "benchmark is now used as Retrieval v3 "
        "development data."
    )

    print()
    print(
        "Only candidate_k changes."
    )

    print(
        "Vector@20, Lexical@20, Path@20, "
        "Best-Rank, reranker model and final "
        "Top5 remain unchanged."
    )

    print()
    print(
        f"{'candidate_k':<14}"
        f"{'Hit@1':<12}"
        f"{'Hit@3':<12}"
        f"{'Hit@5':<12}"
        f"{'Recall@5':<12}"
        f"{'MRR':<10}"
        f"{'Latency ms':<14}"
    )

    print("-" * 118)

    for candidate_k in (
        CANDIDATE_K_VALUES
    ):
        metrics = metrics_by_k[
            candidate_k
        ]

        print(
            f"{candidate_k:<14}"
            f"{percent(metrics.hit_at_1):<12}"
            f"{percent(metrics.hit_at_3):<12}"
            f"{percent(metrics.hit_at_5):<12}"
            f"{percent(metrics.recall_at_5):<12}"
            f"{metrics.mrr:<10.3f}"
            f"{metrics.average_latency_ms:<14.2f}"
        )

    baseline = metrics_by_k[
        10
    ]

    print()
    print(
        "Difference versus candidate_k=10"
    )

    print("-" * 118)

    for candidate_k in (
        15,
        20,
    ):
        metrics = metrics_by_k[
            candidate_k
        ]

        hit_5_delta = (
            metrics.hit_at_5
            - baseline.hit_at_5
        )

        mrr_delta = (
            metrics.mrr
            - baseline.mrr
        )

        latency_delta = (
            metrics.average_latency_ms
            - baseline.average_latency_ms
        )

        latency_ratio = (
            metrics.average_latency_ms
            / baseline.average_latency_ms
            if baseline.average_latency_ms
            > 0
            else 0.0
        )

        print(
            f"candidate_k={candidate_k}"
        )

        print(
            f"  Hit@5 delta:    "
            f"{hit_5_delta * 100:+.2f} pp"
        )

        print(
            f"  MRR delta:      "
            f"{mrr_delta:+.3f}"
        )

        print(
            f"  Latency delta:  "
            f"{latency_delta:+.2f} ms"
        )

        print(
            f"  Latency ratio:  "
            f"{latency_ratio:.2f}x"
        )


def main() -> None:
    suite = load_json(
        SUITE_PATH
    )

    projects_payload = load_json(
        PROJECTS_PATH
    )

    repositories = suite.get(
        "repositories",
    )

    if not isinstance(
        repositories,
        list,
    ):
        raise ValueError(
            "Validation suite does not "
            "contain repositories"
        )

    projects = projects_payload.get(
        "projects",
    )

    if not isinstance(
        projects,
        dict,
    ):
        raise ValueError(
            "Local project mapping does not "
            "contain projects"
        )

    print()
    print("=" * 118)

    print(
        "DEVPILOT AI - "
        "RETRIEVAL V3 CUTOFF EXPERIMENT"
    )

    print("=" * 118)

    print()
    print(
        "Comparing candidate_k: "
        + ", ".join(
            str(value)
            for value in CANDIDATE_K_VALUES
        )
    )

    print(
        f"Rerank model: "
        f"{DEFAULT_RERANK_MODEL}"
    )

    print(
        f"Max chars/document: "
        f"{DEFAULT_MAX_CHARS_PER_DOCUMENT}"
    )

    print(
        f"Final documents: "
        f"{FINAL_K}"
    )

    runs: list[
        RepositoryRun
    ] = []

    for candidate_k in (
        CANDIDATE_K_VALUES
    ):
        print()
        print()
        print("#" * 118)

        print(
            f"EXPERIMENT candidate_k="
            f"{candidate_k}"
        )

        print("#" * 118)

        for repository in repositories:
            if not isinstance(
                repository,
                dict,
            ):
                continue

            repository_key = (
                repository.get(
                    "key",
                )
            )

            dataset_relative_path = (
                repository.get(
                    "dataset",
                )
            )

            if (
                not isinstance(
                    repository_key,
                    str,
                )
                or not isinstance(
                    dataset_relative_path,
                    str,
                )
            ):
                raise ValueError(
                    "Invalid repository entry"
                )

            project_entry = projects.get(
                repository_key,
            )

            if not isinstance(
                project_entry,
                dict,
            ):
                raise ValueError(
                    f"Missing local project "
                    f"mapping: {repository_key}"
                )

            project_id_value = (
                project_entry.get(
                    "project_id",
                )
            )

            if not isinstance(
                project_id_value,
                str,
            ):
                raise ValueError(
                    f"Invalid project_id for "
                    f"{repository_key}"
                )

            project_id = UUID(
                project_id_value
            )

            dataset_path = (
                BACKEND_ROOT
                / dataset_relative_path
            ).resolve()

            print()
            print(
                f"Running {repository_key} "
                f"with candidate_k="
                f"{candidate_k}..."
            )

            db = SessionLocal()

            try:
                retrieve = (
                    build_retrieval_v2_retriever(
                        db=db,
                        project_id=project_id,
                        candidate_k=(
                            candidate_k
                        ),
                        model=(
                            DEFAULT_RERANK_MODEL
                        ),
                        max_chars_per_document=(
                            DEFAULT_MAX_CHARS_PER_DOCUMENT
                        ),
                    )
                )

                report = evaluate_dataset(
                    retrieve=retrieve,
                    retrieval_k=FINAL_K,
                    dataset_path=(
                        dataset_path
                    ),
                )

                repository_results = tuple(
                    report.results
                )

                runs.append(
                    RepositoryRun(
                        repository=(
                            repository_key
                        ),
                        candidate_k=(
                            candidate_k
                        ),
                        results=(
                            repository_results
                        ),
                    )
                )

                print_repository_result(
                    repository=(
                        repository_key
                    ),
                    candidate_k=(
                        candidate_k
                    ),
                    results=(
                        repository_results
                    ),
                )

            finally:
                db.close()

    metrics_by_k: dict[
        int,
        GlobalMetrics,
    ] = {}

    for candidate_k in (
        CANDIDATE_K_VALUES
    ):
        global_results = [
            result
            for run in runs
            if run.candidate_k
            == candidate_k
            for result in run.results
        ]

        metrics = calculate_metrics(
            candidate_k=candidate_k,
            results=global_results,
        )

        metrics_by_k[
            candidate_k
        ] = metrics

        print_global_metrics(
            metrics
        )

    print_comparison(
        metrics_by_k
    )


if __name__ == "__main__":
    main()