from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

from app.db.database import SessionLocal
from evals.evaluator import load_dataset
from evals.lexical_retrieval import build_lexical_retriever
from evals.retrieval_metrics import normalize_path
from evals.vector_candidate_retrieval import (
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


VECTOR_CHUNK_K = 300
VECTOR_DOCUMENT_K = 50
LEXICAL_DOCUMENT_K = 50


TARGET_CASES = {
    "click-core-001",
    "click-decorators-001",
    "click-termui-001",
    "click-testing-001",
    "click-formatting-001",
    "click-utils-001",
    "ky-retry-001",
    "ky-core-001",
    "ky-body-001",
    "ky-normalize-001",
}


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


def main() -> None:
    suite = load_json(
        SUITE_PATH
    )

    projects_config = load_json(
        PROJECTS_PATH
    )

    db = SessionLocal()

    try:
        print()
        print("=" * 100)
        print(
            "DEVPILOT AI - "
            "DEEP CANDIDATE DIAGNOSTIC"
        )
        print("=" * 100)

        print(
            f"Vector chunks:    "
            f"{VECTOR_CHUNK_K}"
        )

        print(
            f"Vector documents: "
            f"{VECTOR_DOCUMENT_K}"
        )

        print(
            f"Lexical documents:"
            f" {LEXICAL_DOCUMENT_K}"
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

            _, _, cases = load_dataset(
                dataset_path
            )

            selected_cases = [
                case
                for case in cases
                if case.id in TARGET_CASES
            ]

            if not selected_cases:
                continue

            vector_retrieve = (
                build_vector_candidate_retriever(
                    db=db,
                    project_id=project_id,
                    chunk_candidate_k=(
                        VECTOR_CHUNK_K
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
            print("=" * 100)

            print(
                f"REPOSITORY: "
                f"{repository_key}"
            )

            print("=" * 100)

            for case in selected_cases:
                expected_file = (
                    case.expected_files[0]
                )

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

                vector_rank = find_rank(
                    vector_files,
                    expected_file,
                )

                lexical_rank = find_rank(
                    lexical_files,
                    expected_file,
                )

                status = (
                    "FOUND"
                    if (
                        vector_rank is not None
                        or lexical_rank is not None
                    )
                    else "MISSING"
                )

                print()
                print(
                    f"{status} "
                    f"{case.id}"
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

        print()
        print("=" * 100)
        print(
            "END DEEP CANDIDATE DIAGNOSTIC"
        )
        print("=" * 100)

    finally:
        db.close()


if __name__ == "__main__":
    main()