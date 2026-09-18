from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

from sqlalchemy import select

from app.db.database import SessionLocal
from app.db.models import Document
from evals.evaluator import load_dataset
from evals.retrieval_metrics import normalize_path


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


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected JSON object: {path}"
        )

    return data


def main() -> None:
    suite = load_json(SUITE_PATH)
    projects_config = load_json(PROJECTS_PATH)

    repositories = suite["repositories"]
    projects = projects_config["projects"]

    db = SessionLocal()

    total_cases = 0
    missing_files: list[
        tuple[str, str, str]
    ] = []

    try:
        for repository in repositories:
            repository_key = repository["key"]

            dataset_path = (
                BACKEND_ROOT
                / repository["dataset"]
            ).resolve()

            project_id = UUID(
                projects[
                    repository_key
                ]["project_id"]
            )

            (
                dataset_name,
                dataset_version,
                cases,
            ) = load_dataset(
                dataset_path
            )

            indexed_paths = set(
                db.scalars(
                    select(Document.path)
                    .where(
                        Document.project_id
                        == project_id
                    )
                ).all()
            )

            normalized_indexed_paths = {
                normalize_path(path)
                for path in indexed_paths
            }

            print()
            print("=" * 90)
            print(
                f"{repository_key} | "
                f"{dataset_name} "
                f"v{dataset_version}"
            )
            print("=" * 90)

            print(
                f"Indexed documents: "
                f"{len(indexed_paths)}"
            )

            for case in cases:
                total_cases += 1

                missing = [
                    expected_path
                    for expected_path
                    in case.expected_files
                    if normalize_path(
                        expected_path
                    )
                    not in normalized_indexed_paths
                ]

                if missing:
                    print(
                        f"FAIL {case.id}"
                    )

                    for path in missing:
                        print(
                            f"  missing: {path}"
                        )

                        missing_files.append(
                            (
                                repository_key,
                                case.id,
                                path,
                            )
                        )
                else:
                    print(
                        f"OK   {case.id}"
                    )

        print()
        print("=" * 90)
        print(
            "INDEPENDENT VALIDATION PREFLIGHT"
        )
        print("=" * 90)

        print(
            f"Cases:          "
            f"{total_cases}"
        )

        print(
            f"Missing files:  "
            f"{len(missing_files)}"
        )

        if missing_files:
            raise RuntimeError(
                "Independent validation "
                "preflight failed"
            )

        print()
        print(
            "READY FOR ONE-SHOT EVALUATION"
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()