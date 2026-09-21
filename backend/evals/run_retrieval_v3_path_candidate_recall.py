from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from app.db.database import SessionLocal
from evals.path_retrieval import (
    DEFAULT_PATH_CANDIDATE_K,
    build_path_retriever,
)
from evals.retrieval_metrics import normalize_path


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


PATH_K = DEFAULT_PATH_CANDIDATE_K


@dataclass(frozen=True)
class CaseResult:
    repository: str
    case_id: str
    category: str
    expected_files: tuple[str, ...]
    retrieved_files: tuple[str, ...]
    expected_ranks: tuple[int | None, ...]

    @property
    def hit(self) -> bool:
        return any(
            rank is not None
            for rank in self.expected_ranks
        )

    @property
    def recall(self) -> float:
        if not self.expected_files:
            return 0.0

        found = sum(
            rank is not None
            for rank in self.expected_ranks
        )

        return (
            found
            / len(self.expected_files)
        )

    @property
    def best_rank(self) -> int | None:
        ranks = [
            rank
            for rank in self.expected_ranks
            if rank is not None
        ]

        if not ranks:
            return None

        return min(
            ranks
        )


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


def get_case_id(
    case: dict,
) -> str:
    value = case.get(
        "id",
    )

    if value is None:
        value = case.get(
            "case_id",
        )

    if (
        not isinstance(
            value,
            str,
        )
        or not value.strip()
    ):
        raise ValueError(
            "Evaluation case has no valid id"
        )

    return value


def get_category(
    case: dict,
) -> str:
    value = case.get(
        "category",
        "",
    )

    if not isinstance(
        value,
        str,
    ):
        return ""

    return value


def get_question(
    case: dict,
) -> str:
    value = case.get(
        "question",
    )

    if (
        not isinstance(
            value,
            str,
        )
        or not value.strip()
    ):
        raise ValueError(
            "Evaluation case has no valid question"
        )

    return value


def get_expected_files(
    case: dict,
) -> tuple[str, ...]:
    value = case.get(
        "expected_files",
    )

    if not isinstance(
        value,
        list,
    ):
        raise ValueError(
            "Evaluation case has no expected_files"
        )

    expected_files = tuple(
        path
        for path in value
        if (
            isinstance(
                path,
                str,
            )
            and path.strip()
        )
    )

    if not expected_files:
        raise ValueError(
            "Evaluation case contains no valid expected files"
        )

    return expected_files


def find_rank(
    retrieved_files: tuple[str, ...],
    expected_file: str,
) -> int | None:
    normalized_expected = normalize_path(
        expected_file
    )

    for rank, retrieved_file in enumerate(
        retrieved_files,
        start=1,
    ):
        if (
            normalize_path(
                retrieved_file
            )
            == normalized_expected
        ):
            return rank

    return None


def evaluate_case(
    *,
    repository: str,
    case: dict,
    retrieve,
) -> CaseResult:
    question = get_question(
        case
    )

    expected_files = get_expected_files(
        case
    )

    retrieved_files = tuple(
        retrieve(
            question,
            PATH_K,
        )
    )

    expected_ranks = tuple(
        find_rank(
            retrieved_files,
            expected_file,
        )
        for expected_file in expected_files
    )

    return CaseResult(
        repository=repository,
        case_id=get_case_id(
            case
        ),
        category=get_category(
            case
        ),
        expected_files=expected_files,
        retrieved_files=retrieved_files,
        expected_ranks=expected_ranks,
    )


def format_rank(
    rank: int | None,
) -> str:
    if rank is None:
        return "MISS"

    return str(
        rank
    )


def print_case_result(
    result: CaseResult,
) -> None:
    status = (
        "HIT"
        if result.hit
        else "MISS"
    )

    print(
        f"{status:<4} "
        f"{result.case_id:<32} "
        f"best_rank="
        f"{format_rank(result.best_rank)}"
    )

    if not result.hit:
        for expected_file in (
            result.expected_files
        ):
            print(
                f"     expected: "
                f"{expected_file}"
            )


def print_repository_summary(
    *,
    repository: str,
    results: list[CaseResult],
) -> None:
    cases = len(
        results
    )

    hits = sum(
        result.hit
        for result in results
    )

    average_recall = (
        sum(
            result.recall
            for result in results
        )
        / cases
        if cases
        else 0.0
    )

    successful_ranks = [
        result.best_rank
        for result in results
        if result.best_rank is not None
    ]

    average_rank = (
        sum(
            successful_ranks
        )
        / len(successful_ranks)
        if successful_ranks
        else 0.0
    )

    print()
    print("-" * 100)

    print(
        f"SUMMARY: {repository}"
    )

    print("-" * 100)

    print(
        f"Cases:           {cases}"
    )

    print(
        f"Path@{PATH_K} hits:   "
        f"{hits}/{cases} "
        f"({hits / cases:.2%})"
    )

    print(
        f"Recall@{PATH_K}:      "
        f"{average_recall:.2%}"
    )

    print(
        f"Avg hit rank:    "
        f"{average_rank:.2f}"
    )


def print_global_summary(
    results: list[CaseResult],
) -> None:
    cases = len(
        results
    )

    hits = sum(
        result.hit
        for result in results
    )

    misses = [
        result
        for result in results
        if not result.hit
    ]

    average_recall = (
        sum(
            result.recall
            for result in results
        )
        / cases
        if cases
        else 0.0
    )

    successful_ranks = [
        result.best_rank
        for result in results
        if result.best_rank is not None
    ]

    average_rank = (
        sum(
            successful_ranks
        )
        / len(successful_ranks)
        if successful_ranks
        else 0.0
    )

    print()
    print()
    print("=" * 100)

    print(
        "DEVPILOT AI - "
        "RETRIEVAL V3 PATH@20 DEVELOPMENT EVALUATION"
    )

    print("=" * 100)

    print()
    print(
        "Dataset status: Retrieval v3 development data"
    )

    print(
        "No embeddings or LLM reranking executed."
    )

    print()
    print(
        f"Cases:               {cases}"
    )

    print(
        f"Path@{PATH_K} hits:       "
        f"{hits}/{cases}"
    )

    print(
        f"Hit@{PATH_K}:             "
        f"{hits / cases:.2%}"
    )

    print(
        f"Recall@{PATH_K}:          "
        f"{average_recall:.2%}"
    )

    print(
        f"Average hit rank:    "
        f"{average_rank:.2f}"
    )

    print(
        f"Misses:              "
        f"{len(misses)}"
    )

    if misses:
        print()
        print(
            "Missed cases"
        )

        print("-" * 100)

        for result in misses:
            print(
                f"{result.repository:<12} "
                f"{result.case_id}"
            )

            for expected_file in (
                result.expected_files
            ):
                print(
                    f"  - {expected_file}"
                )


def main() -> None:
    suite = load_json(
        SUITE_PATH
    )

    mapping = load_json(
        PROJECTS_PATH
    )

    repositories = suite.get(
        "repositories",
    )

    projects = mapping.get(
        "projects",
    )

    if not isinstance(
        repositories,
        list,
    ):
        raise ValueError(
            "Suite does not contain repositories"
        )

    if not isinstance(
        projects,
        dict,
    ):
        raise ValueError(
            "Project mapping does not contain projects"
        )

    all_results: list[
        CaseResult
    ] = []

    print()
    print("=" * 100)

    print(
        "DEVPILOT AI - "
        "RETRIEVAL V3 PATH@20 DEVELOPMENT EVALUATION"
    )

    print("=" * 100)

    print()
    print(
        f"Path candidate depth: "
        f"{PATH_K}"
    )

    print(
        "No OpenAI API calls are performed."
    )

    for repository in repositories:
        if not isinstance(
            repository,
            dict,
        ):
            continue

        repository_key = repository.get(
            "key",
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
                f"Missing project mapping: "
                f"{repository_key}"
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
                f"Invalid project id: "
                f"{repository_key}"
            )

        project_id = UUID(
            project_id_value
        )

        dataset_path = (
            BACKEND_ROOT
            / dataset_relative_path
        ).resolve()

        dataset = load_json(
            dataset_path
        )

        cases = dataset.get(
            "cases",
        )

        if not isinstance(
            cases,
            list,
        ):
            raise ValueError(
                f"Dataset has no cases: "
                f"{dataset_path}"
            )

        print()
        print("=" * 100)

        print(
            f"REPOSITORY: "
            f"{repository_key}"
        )

        print("=" * 100)

        db = SessionLocal()

        repository_results: list[
            CaseResult
        ] = []

        try:
            retrieve = (
                build_path_retriever(
                    db=db,
                    project_id=project_id,
                    candidate_k=PATH_K,
                )
            )

            for case in cases:
                if not isinstance(
                    case,
                    dict,
                ):
                    continue

                result = evaluate_case(
                    repository=(
                        repository_key
                    ),
                    case=case,
                    retrieve=retrieve,
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

        finally:
            db.close()

        print_repository_summary(
            repository=repository_key,
            results=repository_results,
        )

    if len(
        all_results
    ) != 30:
        raise RuntimeError(
            "Expected 30 evaluation cases, "
            f"found {len(all_results)}"
        )

    print_global_summary(
        all_results
    )


if __name__ == "__main__":
    main()