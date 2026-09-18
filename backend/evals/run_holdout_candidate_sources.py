from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

from app.db.database import SessionLocal
from evals.evaluator import load_dataset
from evals.hybrid_retrieval import reciprocal_rank_fusion
from evals.lexical_retrieval import build_lexical_retriever
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
RRF_DOCUMENT_K = 20
RRF_K = 60


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
    config: dict,
    repository_key: str,
) -> UUID:
    return UUID(
        config["projects"][
            repository_key
        ]["project_id"]
    )


def find_rank(
    paths: list[str],
    expected_file: str,
) -> int | None:
    expected = normalize_path(
        expected_file
    )

    for rank, path in enumerate(
        paths,
        start=1,
    ):
        if (
            normalize_path(path)
            == expected
        ):
            return rank

    return None


def merge_unique(
    *groups: list[str],
) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for group in groups:
        for path in group:
            normalized = normalize_path(
                path
            )

            if normalized in seen:
                continue

            seen.add(normalized)
            result.append(path)

    return result


def main() -> None:
    suite = load_json(
        SUITE_PATH
    )

    projects = load_json(
        PROJECTS_PATH
    )

    db = SessionLocal()

    total_cases = 0

    vector_hits = 0
    lexical_hits = 0
    union_hits = 0
    rrf_hits = 0

    failures: list[
        tuple[
            str,
            str,
            str,
            int | None,
            int | None,
            int | None,
        ]
    ] = []

    try:
        print()
        print("=" * 110)
        print(
            "DEVPILOT AI - "
            "HELD-OUT CANDIDATE SOURCE DIAGNOSTIC"
        )
        print("=" * 110)

        print(
            f"Vector documents:  {VECTOR_DOCUMENT_K}"
        )
        print(
            f"Lexical documents: {LEXICAL_DOCUMENT_K}"
        )
        print(
            f"RRF documents:     {RRF_DOCUMENT_K}"
        )
        print(
            f"Vector chunks:     {DEFAULT_CHUNK_CANDIDATE_K}"
        )

        for repository in suite[
            "repositories"
        ]:
            repository_key = (
                repository["key"]
            )

            project_id = get_project_id(
                projects,
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

                union_files = merge_unique(
                    vector_files,
                    lexical_files,
                )

                rrf_results = (
                    reciprocal_rank_fusion(
                        vector_files=vector_files,
                        lexical_files=lexical_files,
                        final_k=RRF_DOCUMENT_K,
                        rrf_k=RRF_K,
                    )
                )

                rrf_files = [
                    result.path
                    for result in rrf_results
                ]

                total_cases += 1

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

                union_rank = find_rank(
                    union_files,
                    expected_file,
                )

                rrf_rank = find_rank(
                    rrf_files,
                    expected_file,
                )

                if vector_rank is not None:
                    vector_hits += 1

                if lexical_rank is not None:
                    lexical_hits += 1

                if union_rank is not None:
                    union_hits += 1

                if rrf_rank is not None:
                    rrf_hits += 1

                status = (
                    "OK"
                    if rrf_rank is not None
                    else "FAIL"
                )

                print()
                print(
                    f"{status} {case.id}"
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
                    f"  Union rank:   "
                    f"{union_rank}"
                )

                print(
                    f"  RRF rank:     "
                    f"{rrf_rank}"
                )

                if rrf_rank is None:
                    failures.append(
                        (
                            repository_key,
                            case.id,
                            expected_file,
                            vector_rank,
                            lexical_rank,
                            union_rank,
                        )
                    )

        print()
        print()
        print("=" * 110)
        print(
            "GLOBAL CANDIDATE SOURCE SUMMARY"
        )
        print("=" * 110)

        print(
            f"Cases:                  "
            f"{total_cases}"
        )

        print()

        print(
            f"Vector Recall@20:       "
            f"{vector_hits / total_cases:.2%} "
            f"({vector_hits}/{total_cases})"
        )

        print(
            f"Lexical Recall@20:      "
            f"{lexical_hits / total_cases:.2%} "
            f"({lexical_hits}/{total_cases})"
        )

        print(
            f"Union Recall:           "
            f"{union_hits / total_cases:.2%} "
            f"({union_hits}/{total_cases})"
        )

        print(
            f"RRF Recall@20:          "
            f"{rrf_hits / total_cases:.2%} "
            f"({rrf_hits}/{total_cases})"
        )

        print()

        print(
            f"RRF failures:           "
            f"{len(failures)}"
        )

        if failures:
            print()
            print("=" * 110)
            print("RRF FAILURE DIAGNOSTIC")
            print("=" * 110)

            for (
                repository_key,
                case_id,
                expected_file,
                vector_rank,
                lexical_rank,
                union_rank,
            ) in failures:
                print()
                print(
                    f"{repository_key} | "
                    f"{case_id}"
                )

                print(
                    f"  Expected:     "
                    f"{expected_file}"
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
                    f"  Union rank:   "
                    f"{union_rank}"
                )

    finally:
        db.close()


if __name__ == "__main__":
    main()