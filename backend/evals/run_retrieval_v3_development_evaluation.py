from __future__ import annotations

import json
import sys
from pathlib import Path
from uuid import UUID

from app.db.database import SessionLocal
from evals.evaluator import (
    EvaluationReport,
    evaluate_dataset,
)
from evals.retrieval_v3 import (
    DEFAULT_RETRIEVAL_V3_CANDIDATE_K,
    build_retrieval_v3_retriever,
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


def print_repository_summary(
    repository: str,
    report: EvaluationReport,
) -> None:
    summary = report.summary

    print()
    print("-" * 100)

    print(
        f"REPOSITORY: {repository}"
    )

    print("-" * 100)

    print(
        f"Cases:      "
        f"{len(report.results)}"
    )

    print(
        f"Hit@1:      "
        f"{summary.hit_at_1:.2%}"
    )

    print(
        f"Hit@3:      "
        f"{summary.hit_at_3:.2%}"
    )

    print(
        f"Hit@5:      "
        f"{summary.hit_at_5:.2%}"
    )

    print(
        f"Recall@5:   "
        f"{summary.recall_at_5:.2%}"
    )

    print(
        f"MRR:        "
        f"{summary.mean_reciprocal_rank:.3f}"
    )

    print(
        f"Latency:    "
        f"{summary.average_latency_ms:.2f} ms"
    )


def main() -> None:
    suite = load_json(
        SUITE_PATH
    )

    projects_payload = load_json(
        PROJECTS_PATH
    )

    repositories = suite.get(
        "repositories"
    )

    projects = projects_payload.get(
        "projects"
    )

    if not isinstance(
        repositories,
        list,
    ):
        raise ValueError(
            "Suite has no valid repositories"
        )

    if not isinstance(
        projects,
        dict,
    ):
        raise ValueError(
            "Project mapping has no valid projects"
        )

    reports: list[
        tuple[str, EvaluationReport]
    ] = []

    print()
    print("=" * 100)

    print(
        "DEVPILOT AI - "
        "RETRIEVAL V3 DEVELOPMENT EVALUATION"
    )

    print("=" * 100)

    print()
    print(
        "IMPORTANT:"
    )

    print(
        "This dataset is Retrieval v3 development data."
    )

    print(
        "It was the independent validation set for v1.1,"
    )

    print(
        "but it has since been inspected and used for tuning."
    )

    print(
        "Results MUST NOT be presented as independent "
        "validation or generalization evidence for v3."
    )

    print()
    print(
        "Configuration"
    )

    print("-" * 100)

    print(
        "Vector candidates:      20"
    )

    print(
        "Lexical candidates:     20"
    )

    print(
        "Path candidates:        20"
    )

    print(
        "Fusion:                 Best-Rank"
    )

    print(
        "Candidates to reranker: "
        f"{DEFAULT_RETRIEVAL_V3_CANDIDATE_K}"
    )

    print(
        f"Final documents:         {FINAL_K}"
    )

    for repository in repositories:
        if not isinstance(
            repository,
            dict,
        ):
            continue

        repository_key = repository.get(
            "key"
        )

        dataset_value = repository.get(
            "dataset"
        )

        if (
            not isinstance(
                repository_key,
                str,
            )
            or not isinstance(
                dataset_value,
                str,
            )
        ):
            raise ValueError(
                "Invalid repository configuration"
            )

        project_entry = projects.get(
            repository_key
        )

        if not isinstance(
            project_entry,
            dict,
        ):
            raise ValueError(
                f"Missing project mapping: "
                f"{repository_key}"
            )

        project_id_value = project_entry.get(
            "project_id"
        )

        if not isinstance(
            project_id_value,
            str,
        ):
            raise ValueError(
                f"Invalid project id: "
                f"{repository_key}"
            )

        project_id = UUID(
            project_id_value
        )

        dataset_path = (
            BACKEND_ROOT
            / dataset_value
        ).resolve()

        print()
        print(
            f"Running {repository_key}..."
        )

        db = SessionLocal()

        try:
            retrieve = (
                build_retrieval_v3_retriever(
                    db=db,
                    project_id=project_id,
                )
            )

            report = evaluate_dataset(
                retrieve=retrieve,
                retrieval_k=FINAL_K,
                dataset_path=dataset_path,
            )

            reports.append(
                (
                    repository_key,
                    report,
                )
            )

            print_repository_summary(
                repository_key,
                report,
            )

        finally:
            db.close()

    total_cases = sum(
        len(
            report.results
        )
        for _, report in reports
    )

    if total_cases != 30:
        raise RuntimeError(
            "Expected 30 evaluation cases, "
            f"found {total_cases}"
        )

    all_results = [
        result
        for _, report in reports
        for result in report.results
    ]

    hit_at_1 = (
        sum(
            result.hit_at_1
            for result in all_results
        )
        / total_cases
    )

    hit_at_3 = (
        sum(
            result.hit_at_3
            for result in all_results
        )
        / total_cases
    )

    hit_at_5 = (
        sum(
            result.hit_at_5
            for result in all_results
        )
        / total_cases
    )

    recall_at_5 = (
        sum(
            result.recall_at_5
            for result in all_results
        )
        / total_cases
    )

    mrr = (
        sum(
            result.reciprocal_rank
            for result in all_results
        )
        / total_cases
    )

    latency = (
        sum(
            result.latency_ms
            for result in all_results
        )
        / total_cases
    )

    failures = [
        result
        for result in all_results
        if result.hit_at_5 == 0
    ]

    print()
    print()
    print("=" * 100)

    print(
        "RETRIEVAL V3 DEVELOPMENT SUMMARY"
    )

    print("=" * 100)

    print()
    print(
        f"Cases:      {total_cases}"
    )

    print(
        f"Hit@1:      {hit_at_1:.2%}"
    )

    print(
        f"Hit@3:      {hit_at_3:.2%}"
    )

    print(
        f"Hit@5:      {hit_at_5:.2%}"
    )

    print(
        f"Recall@5:   {recall_at_5:.2%}"
    )

    print(
        f"MRR:        {mrr:.3f}"
    )

    print(
        f"Latency:    {latency:.2f} ms"
    )

    print(
        f"Failures:   {len(failures)}"
    )

    if failures:
        print()
        print(
            "FAILED CASES"
        )

        print("-" * 100)

        for result in failures:
            print()
            print(
                result.case_id
            )

            print(
                "Expected:"
            )

            for path in result.expected_files:
                print(
                    f"  - {path}"
                )

            print(
                "Retrieved:"
            )

            for index, path in enumerate(
                result.retrieved_files,
                start=1,
            ):
                print(
                    f"  {index}. {path}"
                )

    print()
    print(
        "Methodology note:"
    )

    print(
        "These results are DEVELOPMENT results only."
    )

    print(
        "A new frozen, previously unseen benchmark is "
        "required before making any v3 generalization claim."
    )


if __name__ == "__main__":
    main()