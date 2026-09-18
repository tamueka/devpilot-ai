from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from app.db.database import SessionLocal
from evals.evaluator import (
    EvaluationCase,
    load_dataset,
)
from evals.multi_source_candidate_retrieval import (
    build_multi_source_candidate_collector,
)
from evals.multi_source_fusion import (
    best_rank_fusion,
)
from evals.retrieval_metrics import normalize_path


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

CUTOFFS = (
    10,
    15,
    20,
    30,
    40,
    60,
)

MAX_CUTOFF = max(
    CUTOFFS
)


@dataclass(frozen=True)
class CaseResult:
    repository_key: str
    case_id: str
    expected_files: tuple[str, ...]
    ranked_files: tuple[str, ...]
    first_expected_rank: int | None


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


def calculate_recall(
    retrieved_files: tuple[str, ...],
    expected_files: tuple[str, ...],
) -> float:
    expected = {
        normalize_path(path)
        for path in expected_files
    }

    if not expected:
        return 0.0

    retrieved = {
        normalize_path(path)
        for path in retrieved_files
    }

    relevant = expected.intersection(
        retrieved
    )

    return (
        len(relevant)
        / len(expected)
    )


def find_first_expected_rank(
    retrieved_files: tuple[str, ...],
    expected_files: tuple[str, ...],
) -> int | None:
    expected = {
        normalize_path(path)
        for path in expected_files
    }

    for rank, path in enumerate(
        retrieved_files,
        start=1,
    ):
        if normalize_path(path) in expected:
            return rank

    return None


def evaluate_case(
    *,
    repository_key: str,
    case: EvaluationCase,
    collector,
) -> CaseResult:
    candidates = collector(
        case.question
    )

    fused_results = best_rank_fusion(
        candidates,
        final_k=MAX_CUTOFF,
    )

    ranked_files = tuple(
        result.path
        for result in fused_results
    )

    return CaseResult(
        repository_key=repository_key,
        case_id=case.id,
        expected_files=case.expected_files,
        ranked_files=ranked_files,
        first_expected_rank=(
            find_first_expected_rank(
                ranked_files,
                case.expected_files,
            )
        ),
    )


def print_case_result(
    result: CaseResult,
) -> None:
    print()

    status = (
        "FOUND"
        if result.first_expected_rank
        is not None
        else "MISSING"
    )

    print(
        f"{status} "
        f"{result.case_id}"
    )

    print(
        f"  Best-Rank position: "
        f"{result.first_expected_rank}"
    )

    for cutoff in CUTOFFS:
        recall = calculate_recall(
            result.ranked_files[
                :cutoff
            ],
            result.expected_files,
        )

        print(
            f"  Recall@{cutoff:<2}:        "
            f"{recall:.2%}"
        )


def print_repository_summary(
    *,
    repository_key: str,
    results: list[CaseResult],
) -> None:
    total = len(
        results
    )

    print()
    print("-" * 110)

    print(
        f"SUMMARY: "
        f"{repository_key}"
    )

    print("-" * 110)

    for cutoff in CUTOFFS:
        recall_sum = sum(
            calculate_recall(
                result.ranked_files[
                    :cutoff
                ],
                result.expected_files,
            )
            for result in results
        )

        full_coverage = sum(
            calculate_recall(
                result.ranked_files[
                    :cutoff
                ],
                result.expected_files,
            )
            == 1.0
            for result in results
        )

        average_recall = (
            recall_sum
            / total
            if total
            else 0.0
        )

        print(
            f"Top{cutoff:<2} "
            f"Recall: "
            f"{average_recall:>7.2%} | "
            f"Full coverage: "
            f"{full_coverage}/{total}"
        )


def print_global_summary(
    results: list[CaseResult],
) -> None:
    total = len(
        results
    )

    if total == 0:
        raise ValueError(
            "No evaluation cases found"
        )

    print()
    print()
    print("=" * 110)

    print(
        "DEVPILOT AI - "
        "RETRIEVAL V2 BEST-RANK "
        "CUTOFF EXPERIMENT"
    )

    print("=" * 110)

    print(
        f"Cases: "
        f"{total}"
    )

    print()

    for cutoff in CUTOFFS:
        recall_sum = sum(
            calculate_recall(
                result.ranked_files[
                    :cutoff
                ],
                result.expected_files,
            )
            for result in results
        )

        full_coverage = sum(
            calculate_recall(
                result.ranked_files[
                    :cutoff
                ],
                result.expected_files,
            )
            == 1.0
            for result in results
        )

        average_recall = (
            recall_sum
            / total
        )

        print(
            f"Best-Rank Top{cutoff:<2} "
            f"Recall: "
            f"{average_recall:>7.2%} | "
            f"Full coverage: "
            f"{full_coverage}/{total} "
            f"({full_coverage / total:.2%})"
        )

    print()
    print("Cases outside Top10")
    print("-" * 110)

    outside_top_10 = [
        result
        for result in results
        if (
            result.first_expected_rank
            is None
            or result.first_expected_rank > 10
        )
    ]

    if not outside_top_10:
        print(
            "None"
        )
    else:
        for result in outside_top_10:
            print(
                f"{result.repository_key}"
                f" | "
                f"{result.case_id}"
                f" | rank "
                f"{result.first_expected_rank}"
            )

    print()
    print("Cases outside Top15")
    print("-" * 110)

    outside_top_15 = [
        result
        for result in results
        if (
            result.first_expected_rank
            is None
            or result.first_expected_rank > 15
        )
    ]

    if not outside_top_15:
        print(
            "None"
        )
    else:
        for result in outside_top_15:
            print(
                f"{result.repository_key}"
                f" | "
                f"{result.case_id}"
                f" | rank "
                f"{result.first_expected_rank}"
            )

    print()
    print("Cases outside Top20")
    print("-" * 110)

    outside_top_20 = [
    result
    for result in results
    if (
        result.first_expected_rank is None
        or result.first_expected_rank > 20
    )
]

    if not outside_top_20:
        print(
            "None"
        )
    else:
        for result in outside_top_20:
            print(
                f"{result.repository_key}"
                f" | "
                f"{result.case_id}"
            )


def main() -> None:
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

    all_results: list[
        CaseResult
    ] = []

    try:
        print()
        print("=" * 110)

        print(
            "DEVPILOT AI - "
            "RETRIEVAL V2 BEST-RANK "
            "CUTOFF DIAGNOSTIC"
        )

        print("=" * 110)

        print(
            f"Cutoffs: "
            f"{CUTOFFS}"
        )

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

            raw_dataset_path = (
                repository.get(
                    "dataset"
                )
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

            dataset_path = (
                resolve_dataset_path(
                    raw_dataset_path
                )
            )

            (
                dataset_name,
                dataset_version,
                cases,
            ) = load_dataset(
                dataset_path
            )

            collector = (
                build_multi_source_candidate_collector(
                    db=db,
                    project_id=project_id,
                )
            )

            print()
            print("=" * 110)

            print(
                f"REPOSITORY: "
                f"{repository_key}"
            )

            print("=" * 110)

            print(
                f"Dataset: "
                f"{dataset_name} "
                f"v{dataset_version}"
            )

            repository_results: list[
                CaseResult
            ] = []

            for case in cases:
                result = evaluate_case(
                    repository_key=(
                        repository_key
                    ),
                    case=case,
                    collector=collector,
                )

                repository_results.append(
                    result
                )

                all_results.append(
                    result
                )

                print_case_result(
                    result
                )

            print_repository_summary(
                repository_key=(
                    repository_key
                ),
                results=(
                    repository_results
                ),
            )

        print_global_summary(
            all_results
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()