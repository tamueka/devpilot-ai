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
    DEFAULT_LEXICAL_DOCUMENT_K,
    DEFAULT_PATH_DOCUMENT_K,
    DEFAULT_VECTOR_DOCUMENT_K,
    MultiSourceCandidates,
    build_multi_source_candidate_collector,
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


@dataclass(frozen=True)
class CaseResult:
    repository_key: str
    case_id: str

    vector_recall: float
    lexical_recall: float
    path_recall: float

    vector_lexical_recall: float
    all_sources_recall: float

    vector_rank: int | None
    lexical_rank: int | None
    path_rank: int | None

    rescued_by_path: bool


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


def merge_unique_paths(
    *groups: tuple[str, ...],
) -> tuple[str, ...]:
    merged: list[str] = []
    seen: set[str] = set()

    for group in groups:
        for path in group:
            normalized = normalize_path(
                path
            )

            if normalized in seen:
                continue

            seen.add(
                normalized
            )

            merged.append(
                path
            )

    return tuple(
        merged
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
    candidates: MultiSourceCandidates,
) -> CaseResult:
    vector_lexical_files = (
        merge_unique_paths(
            candidates.vector_files,
            candidates.lexical_files,
        )
    )

    vector_recall = calculate_recall(
        candidates.vector_files,
        case.expected_files,
    )

    lexical_recall = calculate_recall(
        candidates.lexical_files,
        case.expected_files,
    )

    path_recall = calculate_recall(
        candidates.path_files,
        case.expected_files,
    )

    vector_lexical_recall = (
        calculate_recall(
            vector_lexical_files,
            case.expected_files,
        )
    )

    all_sources_recall = (
        calculate_recall(
            candidates.union_files,
            case.expected_files,
        )
    )

    rescued_by_path = (
        vector_lexical_recall < 1.0
        and all_sources_recall == 1.0
    )

    return CaseResult(
        repository_key=repository_key,
        case_id=case.id,
        vector_recall=vector_recall,
        lexical_recall=lexical_recall,
        path_recall=path_recall,
        vector_lexical_recall=(
            vector_lexical_recall
        ),
        all_sources_recall=(
            all_sources_recall
        ),
        vector_rank=find_first_expected_rank(
            candidates.vector_files,
            case.expected_files,
        ),
        lexical_rank=(
            find_first_expected_rank(
                candidates.lexical_files,
                case.expected_files,
            )
        ),
        path_rank=find_first_expected_rank(
            candidates.path_files,
            case.expected_files,
        ),
        rescued_by_path=rescued_by_path,
    )


def print_case_result(
    result: CaseResult,
) -> None:
    status = (
        "OK"
        if result.all_sources_recall == 1.0
        else "FAIL"
    )

    print()
    print(
        f"{status} {result.case_id}"
    )

    print(
        f"  Vector rank:          "
        f"{result.vector_rank}"
    )

    print(
        f"  Lexical rank:         "
        f"{result.lexical_rank}"
    )

    print(
        f"  Path rank:            "
        f"{result.path_rank}"
    )

    print(
        f"  Vector+Lexical:       "
        f"{result.vector_lexical_recall:.2%}"
    )

    print(
        f"  All sources:          "
        f"{result.all_sources_recall:.2%}"
    )

    if result.rescued_by_path:
        print(
            "  Path contribution:    "
            "RESCUED"
        )


def mean(
    values: list[float],
) -> float:
    if not values:
        return 0.0

    return (
        sum(values)
        / len(values)
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

    vector_recall = mean(
        [
            result.vector_recall
            for result in results
        ]
    )

    lexical_recall = mean(
        [
            result.lexical_recall
            for result in results
        ]
    )

    path_recall = mean(
        [
            result.path_recall
            for result in results
        ]
    )

    vector_lexical_recall = mean(
        [
            result.vector_lexical_recall
            for result in results
        ]
    )

    all_sources_recall = mean(
        [
            result.all_sources_recall
            for result in results
        ]
    )

    vector_full = sum(
        result.vector_recall == 1.0
        for result in results
    )

    lexical_full = sum(
        result.lexical_recall == 1.0
        for result in results
    )

    path_full = sum(
        result.path_recall == 1.0
        for result in results
    )

    vector_lexical_full = sum(
        result.vector_lexical_recall == 1.0
        for result in results
    )

    all_sources_full = sum(
        result.all_sources_recall == 1.0
        for result in results
    )

    rescued_by_path = [
        result
        for result in results
        if result.rescued_by_path
    ]

    failures = [
        result
        for result in results
        if result.all_sources_recall < 1.0
    ]

    print()
    print()
    print("=" * 110)

    print(
        "DEVPILOT AI - "
        "RETRIEVAL V2 CANDIDATE COVERAGE"
    )

    print("=" * 110)

    print(
        f"Cases:                         "
        f"{total}"
    )

    print()
    print("Individual sources")
    print("-" * 110)

    print(
        f"Vector Recall@"
        f"{DEFAULT_VECTOR_DOCUMENT_K}:"
        f"              "
        f"{vector_recall:.2%} "
        f"({vector_full}/{total})"
    )

    print(
        f"Lexical Recall@"
        f"{DEFAULT_LEXICAL_DOCUMENT_K}:"
        f"             "
        f"{lexical_recall:.2%} "
        f"({lexical_full}/{total})"
    )

    print(
        f"Path Recall@"
        f"{DEFAULT_PATH_DOCUMENT_K}:"
        f"                "
        f"{path_recall:.2%} "
        f"({path_full}/{total})"
    )

    print()
    print("Candidate pool coverage")
    print("-" * 110)

    print(
        f"Vector + Lexical:              "
        f"{vector_lexical_recall:.2%} "
        f"({vector_lexical_full}/{total})"
    )

    print(
        f"Vector + Lexical + Path:       "
        f"{all_sources_recall:.2%} "
        f"({all_sources_full}/{total})"
    )

    print()
    print("Path contribution")
    print("-" * 110)

    print(
        f"Cases rescued by Path:         "
        f"{len(rescued_by_path)}"
    )

    for result in rescued_by_path:
        print(
            f"  - "
            f"{result.repository_key}"
            f" | "
            f"{result.case_id}"
            f" | Path rank "
            f"{result.path_rank}"
        )

    print()
    print("Remaining failures")
    print("-" * 110)

    print(
        f"Cases still missing:           "
        f"{len(failures)}"
    )

    if not failures:
        print(
            "None"
        )
    else:
        for result in failures:
            print(
                f"  - "
                f"{result.repository_key}"
                f" | "
                f"{result.case_id}"
            )

            print(
                f"      Vector rank:  "
                f"{result.vector_rank}"
            )

            print(
                f"      Lexical rank: "
                f"{result.lexical_rank}"
            )

            print(
                f"      Path rank:    "
                f"{result.path_rank}"
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
            "RETRIEVAL V2 MULTI-SOURCE "
            "CANDIDATE DIAGNOSTIC"
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

            for case in cases:
                candidates = collector(
                    case.question
                )

                result = evaluate_case(
                    repository_key=(
                        repository_key
                    ),
                    case=case,
                    candidates=candidates,
                )

                all_results.append(
                    result
                )

                print_case_result(
                    result
                )

        print_global_summary(
            all_results
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()