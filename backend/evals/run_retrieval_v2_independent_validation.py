from __future__ import annotations

import json
from pathlib import Path
from statistics import fmean
from uuid import UUID

from app.db.database import SessionLocal
from evals.evaluator import (
    CaseEvaluationResult,
    EvaluationReport,
    evaluate_dataset,
)
from evals.llm_reranker import (
    DEFAULT_MAX_CHARS_PER_DOCUMENT,
    DEFAULT_RERANK_MODEL,
)
from evals.multi_source_candidate_retrieval import (
    DEFAULT_LEXICAL_DOCUMENT_K,
    DEFAULT_PATH_DOCUMENT_K,
    DEFAULT_VECTOR_DOCUMENT_K,
)
from evals.retrieval_metrics import normalize_path
from evals.retrieval_v2 import (
    DEFAULT_RETRIEVAL_V2_CANDIDATE_K,
    DEFAULT_RETRIEVAL_V2_FINAL_K,
    build_retrieval_v2_retriever,
)


BACKEND_ROOT = Path(__file__).resolve().parents[1]

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


def load_json(
    path: Path,
) -> dict:
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected JSON object: {path}"
        )

    return data


def print_case_result(
    index: int,
    total: int,
    result: CaseEvaluationResult,
) -> None:
    status = (
        "OK"
        if result.hit_at_5
        else "MISS"
    )

    print()
    print("-" * 110)

    print(
        f"[{index}/{total}] "
        f"{status} "
        f"{result.case_id} | "
        f"{result.category}"
    )

    print("-" * 110)

    print(
        f"Question: {result.question}"
    )

    print()
    print("Expected:")

    for path in result.expected_files:
        print(
            f"  - {path}"
        )

    expected_paths = {
        normalize_path(path)
        for path in result.expected_files
    }

    print()
    print("Retrieved:")

    for position, path in enumerate(
        result.retrieved_files,
        start=1,
    ):
        marker = (
            "*"
            if normalize_path(path)
            in expected_paths
            else " "
        )

        print(
            f"  {marker} "
            f"{position}. {path}"
        )

    print()

    print(
        f"Hit@1:    "
        f"{result.hit_at_1:.0f}"
    )

    print(
        f"Hit@3:    "
        f"{result.hit_at_3:.0f}"
    )

    print(
        f"Hit@5:    "
        f"{result.hit_at_5:.0f}"
    )

    print(
        f"Recall@5: "
        f"{result.recall_at_5:.3f}"
    )

    print(
        f"RR:       "
        f"{result.reciprocal_rank:.3f}"
    )

    print(
        f"Latency:  "
        f"{result.latency_ms:.2f} ms"
    )


def print_repository_summary(
    report: EvaluationReport,
) -> None:
    summary = report.summary

    print()
    print("-" * 110)
    print("REPOSITORY SUMMARY")
    print("-" * 110)

    print(
        f"Cases:               "
        f"{summary.total_cases}"
    )

    print(
        f"Hit@1:               "
        f"{summary.hit_at_1:.2%}"
    )

    print(
        f"Hit@3:               "
        f"{summary.hit_at_3:.2%}"
    )

    print(
        f"Hit@5:               "
        f"{summary.hit_at_5:.2%}"
    )

    print(
        f"Recall@5:            "
        f"{summary.recall_at_5:.2%}"
    )

    print(
        f"MRR:                 "
        f"{summary.mrr:.3f}"
    )

    print(
        f"Unique docs@5:       "
        f"{summary.average_unique_documents_at_5:.2f}"
    )

    print(
        f"Documentation ratio: "
        f"{summary.average_documentation_ratio_at_5:.2%}"
    )

    print(
        f"Code ratio:          "
        f"{summary.average_code_ratio_at_5:.2%}"
    )

    print(
        f"Avg latency:         "
        f"{summary.average_latency_ms:.2f} ms"
    )


def mean_metric(
    results: list[CaseEvaluationResult],
    attribute: str,
) -> float:
    if not results:
        return 0.0

    return fmean(
        float(
            getattr(
                result,
                attribute,
            )
        )
        for result in results
    )


def print_global_summary(
    results: list[CaseEvaluationResult],
    failures: list[
        tuple[
            str,
            CaseEvaluationResult,
        ]
    ],
) -> None:
    print()
    print()
    print("=" * 110)

    print(
        "DEVPILOT AI - "
        "RETRIEVAL V2 "
        "INDEPENDENT VALIDATION"
    )

    print("=" * 110)

    print(
        f"Cases:                         "
        f"{len(results)}"
    )

    print()
    print("Configuration")
    print("-" * 110)

    print(
        f"Vector candidates:             "
        f"{DEFAULT_VECTOR_DOCUMENT_K}"
    )

    print(
        f"Lexical candidates:            "
        f"{DEFAULT_LEXICAL_DOCUMENT_K}"
    )

    print(
        f"Path candidates:               "
        f"{DEFAULT_PATH_DOCUMENT_K}"
    )

    print(
        "Fusion:                        "
        "Best-Rank"
    )

    print(
        f"Candidates to reranker:        "
        f"{DEFAULT_RETRIEVAL_V2_CANDIDATE_K}"
    )

    print(
        f"Final documents:               "
        f"{DEFAULT_RETRIEVAL_V2_FINAL_K}"
    )

    print(
        f"Rerank model:                  "
        f"{DEFAULT_RERANK_MODEL}"
    )

    print(
        f"Max chars/document:            "
        f"{DEFAULT_MAX_CHARS_PER_DOCUMENT}"
    )

    print()
    print("Retrieval quality")
    print("-" * 110)

    print(
        f"Hit@1:                         "
        f"{mean_metric(results, 'hit_at_1'):.2%}"
    )

    print(
        f"Hit@3:                         "
        f"{mean_metric(results, 'hit_at_3'):.2%}"
    )

    print(
        f"Hit@5:                         "
        f"{mean_metric(results, 'hit_at_5'):.2%}"
    )

    print(
        f"Recall@5:                      "
        f"{mean_metric(results, 'recall_at_5'):.2%}"
    )

    print(
        f"MRR:                           "
        f"{mean_metric(results, 'reciprocal_rank'):.3f}"
    )

    print()
    print("Diagnostics")
    print("-" * 110)

    print(
        f"Unique docs@5:                 "
        f"{mean_metric(results, 'unique_documents_at_5'):.2f}"
    )

    print(
        f"Documentation ratio:           "
        f"{mean_metric(results, 'documentation_ratio_at_5'):.2%}"
    )

    print(
        f"Code ratio:                    "
        f"{mean_metric(results, 'code_ratio_at_5'):.2%}"
    )

    print()
    print("Performance")
    print("-" * 110)

    print(
        f"Avg pipeline latency:          "
        f"{mean_metric(results, 'latency_ms'):.2f} ms"
    )

    print()
    print("Independent validation failures")
    print("-" * 110)

    if not failures:
        print(
            "None - all expected files were "
            "retrieved in Top5."
        )
        return

    print(
        f"Failures: "
        f"{len(failures)}"
    )

    for repository_key, result in failures:
        print()
        print(
            f"{repository_key} | "
            f"{result.case_id}"
        )

        print("Expected:")

        for path in result.expected_files:
            print(
                f"  - {path}"
            )

        print("Retrieved:")

        for position, path in enumerate(
            result.retrieved_files,
            start=1,
        ):
            print(
                f"  {position}. {path}"
            )


def main() -> None:
    suite = load_json(
        SUITE_PATH
    )

    projects_config = load_json(
        PROJECTS_PATH
    )

    repositories = suite[
        "repositories"
    ]

    projects = projects_config[
        "projects"
    ]

    all_results: list[
        CaseEvaluationResult
    ] = []

    failures: list[
        tuple[
            str,
            CaseEvaluationResult,
        ]
    ] = []

    print()
    print("=" * 110)

    print(
        "DEVPILOT AI - "
        "RETRIEVAL V2 "
        "INDEPENDENT VALIDATION"
    )

    print("=" * 110)

    print()
    print(
        "Frozen benchmark. "
        "No tuning is performed from these results."
    )

    for repository in repositories:
        repository_key = repository[
            "key"
        ]

        dataset_path = (
            BACKEND_ROOT
            / repository["dataset"]
        ).resolve()

        project_id = UUID(
            projects[
                repository_key
            ]["project_id"]
        )

        print()
        print()
        print("=" * 110)

        print(
            f"REPOSITORY: "
            f"{repository_key}"
        )

        print("=" * 110)

        print(
            f"Source:  "
            f"{repository['source_repository']}"
        )

        print(
            f"Commit:  "
            f"{repository['commit_sha']}"
        )

        print(
            f"Project: "
            f"{project_id}"
        )

        print(
            f"Dataset: "
            f"{dataset_path}"
        )

        db = SessionLocal()

        try:
            retrieve = (
                build_retrieval_v2_retriever(
                    db=db,
                    project_id=project_id,
                    candidate_k=(
                        DEFAULT_RETRIEVAL_V2_CANDIDATE_K
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
                retrieve,
                retrieval_k=(
                    DEFAULT_RETRIEVAL_V2_FINAL_K
                ),
                dataset_path=dataset_path,
            )

        finally:
            db.close()

        total = len(
            report.results
        )

        for index, result in enumerate(
            report.results,
            start=1,
        ):
            print_case_result(
                index=index,
                total=total,
                result=result,
            )

            all_results.append(
                result
            )

            if not result.hit_at_5:
                failures.append(
                    (
                        repository_key,
                        result,
                    )
                )

        print_repository_summary(
            report
        )

    print_global_summary(
        results=all_results,
        failures=failures,
    )


if __name__ == "__main__":
    main()