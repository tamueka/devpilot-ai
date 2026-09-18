from __future__ import annotations

import argparse
import json
from collections.abc import Callable, Sequence
from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models import Project
from evals.evaluator import (
    CaseEvaluationResult,
    EvaluationReport,
    build_summary,
    evaluate_dataset,
)
from evals.hybrid_retrieval import (
    build_hybrid_retriever,
)
from evals.llm_reranker import (
    DEFAULT_MAX_CHARS_PER_DOCUMENT,
    DEFAULT_RERANK_MODEL,
    rerank_candidate_paths,
)
from evals.reranking_candidate_retrieval import (
    DEFAULT_RERANK_CANDIDATE_K,
    build_reranking_candidate_retriever,
)
from evals.vector_retrieval import (
    build_vector_retriever,
)


BACKEND_ROOT = Path(
    __file__
).resolve().parents[1]

DEFAULT_SUITE_PATH = (
    BACKEND_ROOT
    / "evals"
    / "datasets"
    / "holdout_suite.json"
)

DEFAULT_PROJECTS_PATH = (
    BACKEND_ROOT
    / "evals"
    / "datasets"
    / "holdout_projects.local.json"
)

FINAL_K = 5


RetrievalFunction = Callable[
    [str, int],
    Sequence[str],
]


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
        data = json.load(
            file
        )

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
    path = Path(
        value
    )

    if path.is_absolute():
        return path

    return (
        BACKEND_ROOT
        / path
    ).resolve()


def load_project_id(
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
            "holdout_projects.local.json "
            "must contain a projects object"
        )

    project_config = projects.get(
        repository_key
    )

    if not isinstance(
        project_config,
        dict,
    ):
        raise ValueError(
            "Missing local project configuration "
            f"for repository: {repository_key}"
        )

    raw_project_id = project_config.get(
        "project_id"
    )

    if not isinstance(
        raw_project_id,
        str,
    ):
        raise ValueError(
            "Invalid project_id for repository: "
            f"{repository_key}"
        )

    try:
        return UUID(
            raw_project_id
        )
    except ValueError as exc:
        raise ValueError(
            "Invalid UUID for repository "
            f"{repository_key}: "
            f"{raw_project_id}"
        ) from exc


def validate_project(
    db: Session,
    *,
    project_id: UUID,
    repository_key: str,
) -> Project:
    project = db.get(
        Project,
        project_id,
    )

    if project is None:
        raise ValueError(
            "Project not found in database "
            f"for {repository_key}: "
            f"{project_id}"
        )

    status = str(
        project.status
    )

    if status.upper() != "INDEXED":
        raise ValueError(
            f"Project {repository_key} "
            f"is not INDEXED. "
            f"Current status: {status}"
        )

    return project


def build_vector_strategy(
    *,
    db: Session,
    project_id: UUID,
) -> RetrievalFunction:
    return build_vector_retriever(
        db=db,
        project_id=project_id,
    )


def build_hybrid_strategy(
    *,
    db: Session,
    project_id: UUID,
) -> RetrievalFunction:
    return build_hybrid_retriever(
        db=db,
        project_id=project_id,
    )


def build_reranker_strategy(
    *,
    db: Session,
    project_id: UUID,
) -> RetrievalFunction:
    candidate_retrieve = (
        build_reranking_candidate_retriever(
            db=db,
            project_id=project_id,
        )
    )

    def retrieve(
        question: str,
        k: int,
    ) -> list[str]:
        candidate_paths = list(
            candidate_retrieve(
                question,
                DEFAULT_RERANK_CANDIDATE_K,
            )
        )

        return rerank_candidate_paths(
            db=db,
            project_id=project_id,
            question=question,
            candidate_paths=candidate_paths,
            top_k=k,
            model=DEFAULT_RERANK_MODEL,
            max_chars_per_document=(
                DEFAULT_MAX_CHARS_PER_DOCUMENT
            ),
        )

    return retrieve


def build_strategy(
    *,
    strategy: str,
    db: Session,
    project_id: UUID,
) -> RetrievalFunction:
    if strategy == "vector":
        return build_vector_strategy(
            db=db,
            project_id=project_id,
        )

    if strategy == "hybrid":
        return build_hybrid_strategy(
            db=db,
            project_id=project_id,
        )

    if strategy == "reranker":
        return build_reranker_strategy(
            db=db,
            project_id=project_id,
        )

    raise ValueError(
        f"Unsupported strategy: {strategy}"
    )


def print_repository_summary(
    *,
    repository_key: str,
    project: Project,
    project_id: UUID,
    dataset_path: Path,
    report: EvaluationReport,
) -> None:
    summary = report.summary

    print()
    print("=" * 100)

    print(
        f"REPOSITORY: "
        f"{repository_key}"
    )

    print("=" * 100)

    print(
        f"Project name:       "
        f"{project.name}"
    )

    print(
        f"Project ID:         "
        f"{project_id}"
    )

    print(
        f"Dataset:            "
        f"{report.dataset_name}"
    )

    print(
        f"Dataset version:    "
        f"{report.dataset_version}"
    )

    print(
        f"Dataset file:       "
        f"{dataset_path}"
    )

    print(
        f"Cases:              "
        f"{summary.total_cases}"
    )

    print()
    print("Retrieval quality")
    print("-" * 100)

    print(
        f"Hit@1:              "
        f"{summary.hit_at_1:.2%}"
    )

    print(
        f"Hit@3:              "
        f"{summary.hit_at_3:.2%}"
    )

    print(
        f"Hit@5:              "
        f"{summary.hit_at_5:.2%}"
    )

    print(
        f"Recall@5:           "
        f"{summary.recall_at_5:.2%}"
    )

    print(
        f"MRR:                "
        f"{summary.mrr:.3f}"
    )

    print()
    print("Performance")
    print("-" * 100)

    print(
        f"Avg latency:        "
        f"{summary.average_latency_ms:.2f} ms"
    )


def print_global_summary(
    *,
    strategy: str,
    results: list[CaseEvaluationResult],
    repository_count: int,
) -> None:
    summary = build_summary(
        results
    )

    print()
    print()
    print("=" * 100)

    print(
        "DEVPILOT AI - "
        "MULTI-REPOSITORY HOLD-OUT SUMMARY"
    )

    print("=" * 100)

    print(
        f"Strategy:                   "
        f"{strategy}"
    )

    print(
        f"Repositories:               "
        f"{repository_count}"
    )

    print(
        f"Total cases:                "
        f"{summary.total_cases}"
    )

    print()
    print("Global retrieval quality")
    print("-" * 100)

    print(
        f"Hit@1:                      "
        f"{summary.hit_at_1:.2%}"
    )

    print(
        f"Hit@3:                      "
        f"{summary.hit_at_3:.2%}"
    )

    print(
        f"Hit@5:                      "
        f"{summary.hit_at_5:.2%}"
    )

    print(
        f"Recall@5:                   "
        f"{summary.recall_at_5:.2%}"
    )

    print(
        f"MRR:                        "
        f"{summary.mrr:.3f}"
    )

    print()
    print("Diagnostics")
    print("-" * 100)

    print(
        f"Unique docs@5:              "
        f"{summary.average_unique_documents_at_5:.2f}"
    )

    print(
        f"Documentation ratio:        "
        f"{summary.average_documentation_ratio_at_5:.2%}"
    )

    print(
        f"Code ratio:                 "
        f"{summary.average_code_ratio_at_5:.2%}"
    )

    print()
    print("Performance")
    print("-" * 100)

    print(
        f"Avg pipeline latency:       "
        f"{summary.average_latency_ms:.2f} ms"
    )


def run(
    *,
    strategy: str,
    suite_path: Path,
    projects_path: Path,
) -> None:
    suite = load_json(
        suite_path
    )

    projects_config = load_json(
        projects_path
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
            "Hold-out suite must contain "
            "at least one repository"
        )

    db = SessionLocal()

    all_results: list[
        CaseEvaluationResult
    ] = []

    executed_repositories = 0

    try:
        print()
        print("=" * 100)

        print(
            "DEVPILOT AI - "
            "MULTI-REPOSITORY HOLD-OUT"
        )

        print("=" * 100)

        print(
            f"Strategy: "
            f"{strategy}"
        )

        print(
            f"Suite:    "
            f"{suite_path}"
        )

        print()

        for index, repository in enumerate(
            repositories,
            start=1,
        ):
            if not isinstance(
                repository,
                dict,
            ):
                raise ValueError(
                    "Invalid repository "
                    "configuration"
                )

            repository_key = repository.get(
                "key"
            )

            raw_dataset_path = repository.get(
                "dataset"
            )

            if (
                not isinstance(
                    repository_key,
                    str,
                )
                or not repository_key.strip()
            ):
                raise ValueError(
                    "Repository key is missing"
                )

            if (
                not isinstance(
                    raw_dataset_path,
                    str,
                )
                or not raw_dataset_path.strip()
            ):
                raise ValueError(
                    "Dataset path is missing for "
                    f"{repository_key}"
                )

            project_id = load_project_id(
                projects_config,
                repository_key,
            )

            project = validate_project(
                db,
                project_id=project_id,
                repository_key=(
                    repository_key
                ),
            )

            dataset_path = (
                resolve_dataset_path(
                    raw_dataset_path
                )
            )

            print(
                f"[{index}/{len(repositories)}] "
                f"{repository_key}"
            )

            retrieve = build_strategy(
                strategy=strategy,
                db=db,
                project_id=project_id,
            )

            report = evaluate_dataset(
                retrieve=retrieve,
                retrieval_k=FINAL_K,
                dataset_path=dataset_path,
            )

            if (
                report.summary.total_cases
                == 0
            ):
                raise ValueError(
                    "Held-out dataset contains "
                    "zero evaluation cases: "
                    f"{dataset_path}"
                )

            print_repository_summary(
                repository_key=(
                    repository_key
                ),
                project=project,
                project_id=project_id,
                dataset_path=dataset_path,
                report=report,
            )

            all_results.extend(
                report.results
            )

            executed_repositories += 1

        print_global_summary(
            strategy=strategy,
            results=all_results,
            repository_count=(
                executed_repositories
            ),
        )

    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Ejecuta el benchmark held-out "
            "multi-repositorio de DevPilot AI."
        )
    )

    parser.add_argument(
        "--strategy",
        required=True,
        choices=(
            "vector",
            "hybrid",
            "reranker",
        ),
        help=(
            "Estrategia de retrieval que se "
            "evaluará sobre todos los repositorios."
        ),
    )

    parser.add_argument(
        "--suite",
        type=Path,
        default=DEFAULT_SUITE_PATH,
        help=(
            "Configuración de la suite "
            "multi-repositorio."
        ),
    )

    parser.add_argument(
        "--projects",
        type=Path,
        default=DEFAULT_PROJECTS_PATH,
        help=(
            "Configuración local que relaciona "
            "repositorios con Project IDs."
        ),
    )

    args = parser.parse_args()

    run(
        strategy=args.strategy,
        suite_path=args.suite.resolve(),
        projects_path=(
            args.projects.resolve()
        ),
    )


if __name__ == "__main__":
    main()