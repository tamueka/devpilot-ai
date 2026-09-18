from __future__ import annotations

import argparse
import json
from pathlib import Path
from uuid import UUID

from app.db.database import SessionLocal
from evals.evaluator import (
    EvaluationReport,
    evaluate_dataset,
)
from evals.llm_reranker import (
    DEFAULT_MAX_CHARS_PER_DOCUMENT,
    DEFAULT_RERANK_MODEL,
)
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
    / "holdout_suite.json"
)

PROJECTS_PATH = (
    BACKEND_ROOT
    / "evals"
    / "datasets"
    / "holdout_projects.local.json"
)


def load_json(
    path: Path,
) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            f"Expected JSON object: {path}"
        )

    return data


def resolve_dataset_path(
    value: str,
) -> Path:
    path = Path(value)

    if path.is_absolute():
        return path

    return (
        BACKEND_ROOT
        / path
    ).resolve()


def get_project_id(
    projects_config: dict,
    repository_key: str,
) -> UUID:
    projects = projects_config.get(
        "projects"
    )

    if not isinstance(
        projects,
        dict,
    ):
        raise ValueError(
            "projects configuration is missing"
        )

    project_config = projects.get(
        repository_key
    )

    if not isinstance(
        project_config,
        dict,
    ):
        raise ValueError(
            "Missing project configuration for "
            f"{repository_key}"
        )

    raw_project_id = project_config.get(
        "project_id"
    )

    if not isinstance(
        raw_project_id,
        str,
    ):
        raise ValueError(
            "Invalid project_id for "
            f"{repository_key}"
        )

    return UUID(
        raw_project_id
    )


def print_case_results(
    report: EvaluationReport,
) -> None:
    total = len(
        report.results
    )

    for index, result in enumerate(
        report.results,
        start=1,
    ):
        status = (
            "OK"
            if result.hit_at_5
            else "FAIL"
        )

        print()
        print(
            f"[{index}/{total}] "
            f"{status} "
            f"{result.case_id}"
        )

        print(
            f"  Hit@1:    "
            f"{result.hit_at_1:.0f}"
        )

        print(
            f"  Hit@3:    "
            f"{result.hit_at_3:.0f}"
        )

        print(
            f"  Hit@5:    "
            f"{result.hit_at_5:.0f}"
        )

        print(
            f"  Recall@5: "
            f"{result.recall_at_5:.3f}"
        )

        print(
            f"  RR:       "
            f"{result.reciprocal_rank:.3f}"
        )

        print(
            f"  Latency:  "
            f"{result.latency_ms:.2f} ms"
        )

        print(
            "  Retrieved:"
        )

        for position, path in enumerate(
            result.retrieved_files,
            start=1,
        ):
            print(
                f"    {position}. "
                f"{path}"
            )


def print_repository_summary(
    *,
    repository_key: str,
    report: EvaluationReport,
) -> None:
    summary = report.summary

    print()
    print("-" * 110)

    print(
        f"SUMMARY: "
        f"{repository_key}"
    )

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


def weighted_average(
    reports: list[EvaluationReport],
    attribute: str,
) -> float:
    total_cases = sum(
        report.summary.total_cases
        for report in reports
    )

    if total_cases == 0:
        return 0.0

    weighted_sum = sum(
        getattr(
            report.summary,
            attribute,
        )
        * report.summary.total_cases
        for report in reports
    )

    return (
        weighted_sum
        / total_cases
    )


def print_global_summary(
    *,
    reports: list[EvaluationReport],
    model: str,
    candidate_k: int,
    max_chars_per_document: int,
) -> None:
    total_cases = sum(
        report.summary.total_cases
        for report in reports
    )

    print()
    print()
    print("=" * 110)

    print(
        "DEVPILOT AI - "
        "RETRIEVAL V2 HOLDOUT RESULTS"
    )

    print("=" * 110)

    print(
        f"Cases:                         "
        f"{total_cases}"
    )

    print()
    print("Configuration")
    print("-" * 110)

    print(
        f"Vector candidates:             "
        f"20"
    )

    print(
        f"Lexical candidates:            "
        f"20"
    )

    print(
        f"Path candidates:               "
        f"20"
    )

    print(
        f"Fusion:                        "
        f"Best-Rank"
    )

    print(
        f"Candidates to reranker:        "
        f"{candidate_k}"
    )

    print(
        f"Final documents:               "
        f"{DEFAULT_RETRIEVAL_V2_FINAL_K}"
    )

    print(
        f"Rerank model:                  "
        f"{model}"
    )

    print(
        f"Max chars/document:            "
        f"{max_chars_per_document}"
    )

    print()
    print("Retrieval quality")
    print("-" * 110)

    print(
        f"Hit@1:                         "
        f"{weighted_average(reports, 'hit_at_1'):.2%}"
    )

    print(
        f"Hit@3:                         "
        f"{weighted_average(reports, 'hit_at_3'):.2%}"
    )

    print(
        f"Hit@5:                         "
        f"{weighted_average(reports, 'hit_at_5'):.2%}"
    )

    print(
        f"Recall@5:                      "
        f"{weighted_average(reports, 'recall_at_5'):.2%}"
    )

    print(
        f"MRR:                           "
        f"{weighted_average(reports, 'mrr'):.3f}"
    )

    print()
    print("Diagnostics")
    print("-" * 110)

    print(
        f"Unique docs@5:                 "
        f"{weighted_average(reports, 'average_unique_documents_at_5'):.2f}"
    )

    print(
        f"Documentation ratio:           "
        f"{weighted_average(reports, 'average_documentation_ratio_at_5'):.2%}"
    )

    print(
        f"Code ratio:                    "
        f"{weighted_average(reports, 'average_code_ratio_at_5'):.2%}"
    )

    print()
    print("Performance")
    print("-" * 110)

    print(
        f"Avg pipeline latency:          "
        f"{weighted_average(reports, 'average_latency_ms'):.2f} ms"
    )


def run(
    *,
    model: str,
    candidate_k: int,
    max_chars_per_document: int,
) -> None:
    suite = load_json(
        SUITE_PATH
    )

    projects_config = load_json(
        PROJECTS_PATH
    )

    repositories = suite.get(
        "repositories"
    )

    if (
        not isinstance(
            repositories,
            list,
        )
        or not repositories
    ):
        raise ValueError(
            "holdout suite contains no repositories"
        )

    db = SessionLocal()

    reports: list[
        EvaluationReport
    ] = []

    try:
        print()
        print("=" * 110)

        print(
            "DEVPILOT AI - "
            "RETRIEVAL V2 HOLDOUT EVALUATION"
        )

        print("=" * 110)

        for repository in repositories:
            if not isinstance(
                repository,
                dict,
            ):
                raise ValueError(
                    "Invalid repository configuration"
                )

            repository_key = repository.get(
                "key"
            )

            raw_dataset_path = repository.get(
                "dataset"
            )

            if not isinstance(
                repository_key,
                str,
            ):
                raise ValueError(
                    "Repository key is missing"
                )

            if not isinstance(
                raw_dataset_path,
                str,
            ):
                raise ValueError(
                    "Repository dataset is missing"
                )

            project_id = get_project_id(
                projects_config,
                repository_key,
            )

            dataset_path = resolve_dataset_path(
                raw_dataset_path
            )

            retrieve = build_retrieval_v2_retriever(
                db=db,
                project_id=project_id,
                candidate_k=candidate_k,
                model=model,
                max_chars_per_document=(
                    max_chars_per_document
                ),
            )

            print()
            print("=" * 110)

            print(
                f"REPOSITORY: "
                f"{repository_key}"
            )

            print("=" * 110)

            report = evaluate_dataset(
                retrieve=retrieve,
                retrieval_k=(
                    DEFAULT_RETRIEVAL_V2_FINAL_K
                ),
                dataset_path=dataset_path,
            )

            reports.append(
                report
            )

            print_case_results(
                report
            )

            print_repository_summary(
                repository_key=(
                    repository_key
                ),
                report=report,
            )

        print_global_summary(
            reports=reports,
            model=model,
            candidate_k=candidate_k,
            max_chars_per_document=(
                max_chars_per_document
            ),
        )

    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Evalúa Retrieval v2: "
            "Vector + Lexical + Path + "
            "Best-Rank + LLM reranker."
        )
    )

    parser.add_argument(
        "--model",
        default=DEFAULT_RERANK_MODEL,
        help=(
            "Modelo utilizado por el reranker."
        ),
    )

    parser.add_argument(
        "--candidate-k",
        type=int,
        default=(
            DEFAULT_RETRIEVAL_V2_CANDIDATE_K
        ),
        help=(
            "Número de candidatos Best-Rank "
            "enviados al reranker. "
            "Por defecto: 10."
        ),
    )

    parser.add_argument(
        "--max-chars-per-document",
        type=int,
        default=DEFAULT_MAX_CHARS_PER_DOCUMENT,
        help=(
            "Máximo de caracteres por documento."
        ),
    )

    args = parser.parse_args()

    if args.candidate_k <= 0:
        parser.error(
            "--candidate-k debe ser mayor que cero"
        )

    if (
        args.max_chars_per_document
        <= 0
    ):
        parser.error(
            "--max-chars-per-document "
            "debe ser mayor que cero"
        )

    if not args.model.strip():
        parser.error(
            "--model no puede estar vacío"
        )

    run(
        model=args.model,
        candidate_k=args.candidate_k,
        max_chars_per_document=(
            args.max_chars_per_document
        ),
    )


if __name__ == "__main__":
    main()