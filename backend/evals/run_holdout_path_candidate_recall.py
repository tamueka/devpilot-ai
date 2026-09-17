from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

from app.db.database import SessionLocal
from evals.evaluator import load_dataset
from evals.lexical_retrieval import build_lexical_retriever
from evals.path_retrieval import build_path_retriever
from evals.retrieval_metrics import normalize_path
from evals.vector_candidate_retrieval import (
    DEFAULT_CHUNK_CANDIDATE_K,
    build_vector_candidate_retriever,
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

VECTOR_DOCUMENT_K = 20
LEXICAL_DOCUMENT_K = 20
PATH_DOCUMENT_K = 20


def load_json(path: Path) -> dict:
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


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
    return UUID(
        projects_config["projects"][
            repository_key
        ]["project_id"]
    )


def merge_unique(
    *groups: list[str],
) -> list[str]:
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

    return merged


def recall(
    retrieved_files: list[str],
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

    return (
        len(
            expected.intersection(
                retrieved
            )
        )
        / len(expected)
    )


def find_rank(
    retrieved_files: list[str],
    expected_file: str,
) -> int | None:
    expected = normalize_path(
        expected_file
    )

    for rank, path in enumerate(
        retrieved_files,
        start=1,
    ):
        if (
            normalize_path(path)
            == expected
        ):
            return rank

    return None


def main() -> None:
    suite = load_json(
        SUITE_PATH
    )

    projects_config = load_json(
        PROJECTS_PATH
    )

    db = SessionLocal()

    total_cases = 0

    vector_full = 0
    lexical_full = 0
    path_full = 0

    vector_lexical_full = 0
    all_sources_full = 0

    vector_recall_sum = 0.0
    lexical_recall_sum = 0.0
    path_recall_sum = 0.0

    vector_lexical_recall_sum = 0.0
    all_sources_recall_sum = 0.0

    remaining_failures: list[
        tuple[
            str,
            str,
            tuple[str, ...],
            list[str],
            list[str],
            list[str],
        ]
    ] = []

    try:
        print()
        print("=" * 110)
        print(
            "DEVPILOT AI - "
            "PATH-AWARE CANDIDATE RECALL"
        )
        print("=" * 110)

        print(
            f"Vector chunks:     "
            f"{DEFAULT_CHUNK_CANDIDATE_K}"
        )

        print(
            f"Vector documents:  "
            f"{VECTOR_DOCUMENT_K}"
        )

        print(
            f"Lexical documents: "
            f"{LEXICAL_DOCUMENT_K}"
        )

        print(
            f"Path documents:    "
            f"{PATH_DOCUMENT_K}"
        )

        for repository in suite[
            "repositories"
        ]:
            repository_key = (
                repository["key"]
            )

            project_id = get_project_id(
                projects_config,
                repository_key,
            )

            dataset_path = (
                resolve_dataset_path(
                    repository["dataset"]
                )
            )

            (
                dataset_name,
                dataset_version,
                cases,
            ) = load_dataset(
                dataset_path
            )

            vector_retrieve = (
                build_vector_candidate_retriever(
                    db=db,
                    project_id=project_id,
                    chunk_candidate_k=(
                        DEFAULT_CHUNK_CANDIDATE_K
                    ),
                )
            )

            lexical_retrieve = (
                build_lexical_retriever(
                    db=db,
                    project_id=project_id,
                    candidate_k=(
                        LEXICAL_DOCUMENT_K
                    ),
                )
            )

            path_retrieve = (
                build_path_retriever(
                    db=db,
                    project_id=project_id,
                    candidate_k=(
                        PATH_DOCUMENT_K
                    ),
                )
            )

            repo_total = 0
            repo_all_sources_full = 0

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
                vector_files = list(
                    vector_retrieve(
                        case.question,
                        VECTOR_DOCUMENT_K,
                    )
                )

                lexical_files = list(
                    lexical_retrieve(
                        case.question,
                        LEXICAL_DOCUMENT_K,
                    )
                )

                path_files = list(
                    path_retrieve(
                        case.question,
                        PATH_DOCUMENT_K,
                    )
                )

                vector_lexical_files = (
                    merge_unique(
                        vector_files,
                        lexical_files,
                    )
                )

                all_source_files = (
                    merge_unique(
                        vector_files,
                        lexical_files,
                        path_files,
                    )
                )

                vector_case_recall = recall(
                    vector_files,
                    case.expected_files,
                )

                lexical_case_recall = recall(
                    lexical_files,
                    case.expected_files,
                )

                path_case_recall = recall(
                    path_files,
                    case.expected_files,
                )

                vector_lexical_case_recall = (
                    recall(
                        vector_lexical_files,
                        case.expected_files,
                    )
                )

                all_sources_case_recall = (
                    recall(
                        all_source_files,
                        case.expected_files,
                    )
                )

                total_cases += 1
                repo_total += 1

                vector_recall_sum += (
                    vector_case_recall
                )

                lexical_recall_sum += (
                    lexical_case_recall
                )

                path_recall_sum += (
                    path_case_recall
                )

                vector_lexical_recall_sum += (
                    vector_lexical_case_recall
                )

                all_sources_recall_sum += (
                    all_sources_case_recall
                )

                if vector_case_recall == 1.0:
                    vector_full += 1

                if lexical_case_recall == 1.0:
                    lexical_full += 1

                if path_case_recall == 1.0:
                    path_full += 1

                if (
                    vector_lexical_case_recall
                    == 1.0
                ):
                    vector_lexical_full += 1

                if (
                    all_sources_case_recall
                    == 1.0
                ):
                    all_sources_full += 1
                    repo_all_sources_full += 1
                else:
                    remaining_failures.append(
                        (
                            repository_key,
                            case.id,
                            case.expected_files,
                            vector_files,
                            lexical_files,
                            path_files,
                        )
                    )

                expected_file = (
                    case.expected_files[0]
                )

                vector_rank = find_rank(
                    vector_files,
                    expected_file,
                )

                lexical_rank = find_rank(
                    lexical_files,
                    expected_file,
                )

                path_rank = find_rank(
                    path_files,
                    expected_file,
                )

                status = (
                    "OK"
                    if (
                        all_sources_case_recall
                        == 1.0
                    )
                    else "FAIL"
                )

                print()
                print(
                    f"{status} "
                    f"{case.id}"
                )

                print(
                    f"  Vector rank:  "
                    f"{vector_rank}"
                )

                print(
                    f"  Lexical rank: "
                    f"{lexical_rank}"
                )

                print(
                    f"  Path rank:    "
                    f"{path_rank}"
                )

            print()
            print(
                f"Repository coverage "
                f"(all sources): "
                f"{repo_all_sources_full}/"
                f"{repo_total}"
            )

        print()
        print()
        print("=" * 110)
        print(
            "GLOBAL PATH-AWARE "
            "CANDIDATE SUMMARY"
        )
        print("=" * 110)

        print(
            f"Cases:                         "
            f"{total_cases}"
        )

        print()

        print(
            f"Vector Recall@20:              "
            f"{vector_recall_sum / total_cases:.2%}"
        )

        print(
            f"Lexical Recall@20:             "
            f"{lexical_recall_sum / total_cases:.2%}"
        )

        print(
            f"Path Recall@20:                "
            f"{path_recall_sum / total_cases:.2%}"
        )

        print()

        print(
            f"Vector + Lexical Recall:       "
            f"{vector_lexical_recall_sum / total_cases:.2%}"
        )

        print(
            f"Vector + Lexical + Path:       "
            f"{all_sources_recall_sum / total_cases:.2%}"
        )

        print()
        print("Full coverage")
        print("-" * 110)

        print(
            f"Vector:                        "
            f"{vector_full}/{total_cases}"
        )

        print(
            f"Lexical:                       "
            f"{lexical_full}/{total_cases}"
        )

        print(
            f"Path:                          "
            f"{path_full}/{total_cases}"
        )

        print(
            f"Vector + Lexical:              "
            f"{vector_lexical_full}/"
            f"{total_cases}"
        )

        print(
            f"Vector + Lexical + Path:       "
            f"{all_sources_full}/"
            f"{total_cases}"
        )

        print()

        print(
            f"Remaining failures:            "
            f"{len(remaining_failures)}"
        )

        if remaining_failures:
            print()
            print("=" * 110)
            print(
                "REMAINING FAILURE DIAGNOSTIC"
            )
            print("=" * 110)

            for (
                repository_key,
                case_id,
                expected_files,
                vector_files,
                lexical_files,
                path_files,
            ) in remaining_failures:
                print()
                print(
                    f"{repository_key} | "
                    f"{case_id}"
                )

                for expected_file in (
                    expected_files
                ):
                    print(
                        f"  Expected: "
                        f"{expected_file}"
                    )

                    print(
                        f"  Vector:  "
                        f"{find_rank(vector_files, expected_file)}"
                    )

                    print(
                        f"  Lexical: "
                        f"{find_rank(lexical_files, expected_file)}"
                    )

                    print(
                        f"  Path:    "
                        f"{find_rank(path_files, expected_file)}"
                    )

    finally:
        db.close()


if __name__ == "__main__":
    main()