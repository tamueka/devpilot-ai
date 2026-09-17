from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models import Project
from evals.evaluator import load_dataset
from evals.retrieval_metrics import normalize_path
from evals.reranking_candidate_retrieval import (
    DEFAULT_RERANK_CANDIDATE_K,
    build_reranking_candidate_retriever,
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


def load_json(path: Path) -> dict:
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def resolve_dataset_path(
    dataset: str,
) -> Path:
    path = Path(dataset)

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
        projects_config[
            "projects"
        ][
            repository_key
        ][
            "project_id"
        ]
    )


def candidate_recall(
    retrieved_files: list[str],
    expected_files: tuple[str, ...],
) -> float:
    expected = {
        normalize_path(path)
        for path in expected_files
    }

    retrieved = {
        normalize_path(path)
        for path in retrieved_files
    }

    if not expected:
        return 0.0

    return (
        len(
            expected.intersection(
                retrieved
            )
        )
        / len(expected)
    )


def expected_ranks(
    retrieved_files: list[str],
    expected_files: tuple[str, ...],
) -> dict[str, int | None]:
    positions = {
        normalize_path(path): rank
        for rank, path in enumerate(
            retrieved_files,
            start=1,
        )
    }

    return {
        expected_file: positions.get(
            normalize_path(
                expected_file
            )
        )
        for expected_file in expected_files
    }


def validate_project(
    db: Session,
    project_id: UUID,
) -> Project:
    project = db.get(
        Project,
        project_id,
    )

    if project is None:
        raise ValueError(
            f"Project not found: {project_id}"
        )

    return project


def main() -> None:
    suite = load_json(
        SUITE_PATH
    )

    projects_config = load_json(
        PROJECTS_PATH
    )

    db = SessionLocal()

    total_cases = 0
    full_coverage_cases = 0
    recall_sum = 0.0

    repository_results: list[
        tuple[
            str,
            int,
            int,
            float,
        ]
    ] = []

    failures: list[
        tuple[
            str,
            str,
            tuple[str, ...],
            list[str],
        ]
    ] = []

    try:
        print()
        print("=" * 100)

        print(
            "DEVPILOT AI - "
            "HELD-OUT RRF CANDIDATE RECALL"
        )

        print("=" * 100)

        print(
            "Candidate cutoff: "
            f"Top{DEFAULT_RERANK_CANDIDATE_K}"
        )

        for repository in suite[
            "repositories"
        ]:
            repository_key = repository[
                "key"
            ]

            project_id = get_project_id(
                projects_config,
                repository_key,
            )

            project = validate_project(
                db,
                project_id,
            )

            dataset_path = (
                resolve_dataset_path(
                    repository[
                        "dataset"
                    ]
                )
            )

            (
                dataset_name,
                dataset_version,
                cases,
            ) = load_dataset(
                dataset_path
            )

            retrieve = (
                build_reranking_candidate_retriever(
                    db=db,
                    project_id=project_id,
                )
            )

            repo_total = 0
            repo_full = 0
            repo_recall_sum = 0.0

            print()
            print("=" * 100)

            print(
                f"REPOSITORY: "
                f"{repository_key}"
            )

            print("=" * 100)

            print(
                f"Project: "
                f"{project.name}"
            )

            print(
                f"Dataset: "
                f"{dataset_name} "
                f"v{dataset_version}"
            )

            for case in cases:
                candidates = list(
                    retrieve(
                        case.question,
                        DEFAULT_RERANK_CANDIDATE_K,
                    )
                )

                recall = candidate_recall(
                    candidates,
                    case.expected_files,
                )

                ranks = expected_ranks(
                    candidates,
                    case.expected_files,
                )

                full_coverage = (
                    recall == 1.0
                )

                repo_total += 1
                total_cases += 1

                repo_recall_sum += recall
                recall_sum += recall

                if full_coverage:
                    repo_full += 1
                    full_coverage_cases += 1
                else:
                    failures.append(
                        (
                            repository_key,
                            case.id,
                            case.expected_files,
                            candidates,
                        )
                    )

                status = (
                    "✓"
                    if full_coverage
                    else "✗"
                )

                print()
                print(
                    f"{status} "
                    f"{case.id}"
                )

                print(
                    f"  Recall@"
                    f"{DEFAULT_RERANK_CANDIDATE_K}: "
                    f"{recall:.2%}"
                )

                for (
                    expected_file,
                    rank,
                ) in ranks.items():
                    print(
                        f"  Expected: "
                        f"{expected_file}"
                    )

                    print(
                        f"  Rank:     "
                        f"{rank}"
                    )

            repository_results.append(
                (
                    repository_key,
                    repo_total,
                    repo_full,
                    (
                        repo_recall_sum
                        / repo_total
                    ),
                )
            )

        print()
        print()
        print("=" * 100)

        print(
            "HELD-OUT CANDIDATE "
            "RECALL SUMMARY"
        )

        print("=" * 100)

        for (
            repository_key,
            repo_total,
            repo_full,
            repo_recall,
        ) in repository_results:
            print(
                f"{repository_key:<25} "
                f"Recall@"
                f"{DEFAULT_RERANK_CANDIDATE_K}: "
                f"{repo_recall:>7.2%} | "
                f"Full coverage: "
                f"{repo_full}/{repo_total}"
            )

        print()
        print("-" * 100)

        global_recall = (
            recall_sum
            / total_cases
        )

        print(
            f"Global Recall@"
            f"{DEFAULT_RERANK_CANDIDATE_K}: "
            f"{global_recall:.2%}"
        )

        print(
            f"Full coverage: "
            f"{full_coverage_cases}/"
            f"{total_cases} "
            f"("
            f"{full_coverage_cases / total_cases:.2%}"
            f")"
        )

        print()
        print(
            "Candidate failures: "
            f"{len(failures)}"
        )

        if failures:
            print()
            print("=" * 100)
            print(
                "FAILED CASES"
            )
            print("=" * 100)

            for (
                repository_key,
                case_id,
                expected_files,
                candidates,
            ) in failures:
                print()
                print(
                    f"{repository_key} "
                    f"| {case_id}"
                )

                print(
                    "Expected:"
                )

                for expected_file in (
                    expected_files
                ):
                    print(
                        f"  - "
                        f"{expected_file}"
                    )

                print(
                    f"Top"
                    f"{DEFAULT_RERANK_CANDIDATE_K}:"
                )

                for index, path in enumerate(
                    candidates,
                    start=1,
                ):
                    print(
                        f"  {index:>2}. "
                        f"{path}"
                    )

    finally:
        db.close()


if __name__ == "__main__":
    main()