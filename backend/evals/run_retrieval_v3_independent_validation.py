from __future__ import annotations

import json
import sys
from pathlib import Path
from uuid import UUID

from sqlalchemy import select

from app.db.database import SessionLocal
from app.db.models import Document
from evals.evaluator import (
    EvaluationReport,
    evaluate_dataset,
)
from evals.retrieval_metrics import (
    normalize_path,
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
    / "v3_independent"
    / "suite.json"
)

PROJECTS_PATH = (
    BACKEND_ROOT
    / "evals"
    / "datasets"
    / "v3_independent_projects.local.json"
)

FINAL_K = 5


def load_json(
    path: Path,
) -> dict:
    if not path.is_file():
        raise RuntimeError(
            f"No existe el fichero requerido: {path}"
        )

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
        raise RuntimeError(
            f"JSON inválido: {path}"
        )

    return payload


def load_expected_files(
    dataset_path: Path,
) -> set[str]:
    dataset = load_json(
        dataset_path
    )

    cases = dataset.get(
        "cases"
    )

    if not isinstance(
        cases,
        list,
    ):
        raise RuntimeError(
            f"Dataset sin casos: {dataset_path}"
        )

    expected: set[str] = set()

    for case in cases:
        if not isinstance(
            case,
            dict,
        ):
            continue

        files = case.get(
            "expected_files"
        )

        if not isinstance(
            files,
            list,
        ):
            raise RuntimeError(
                "Caso sin expected_files"
            )

        for path in files:
            if (
                isinstance(
                    path,
                    str,
                )
                and path.strip()
            ):
                expected.add(
                    normalize_path(
                        path
                    )
                )

    return expected


def get_project_id(
    projects: dict,
    repository_key: str,
) -> UUID:
    entry = projects.get(
        repository_key
    )

    if not isinstance(
        entry,
        dict,
    ):
        raise RuntimeError(
            "Falta project mapping para "
            f"{repository_key}"
        )

    value = entry.get(
        "project_id"
    )

    if (
        not isinstance(
            value,
            str,
        )
        or not value.strip()
    ):
        raise RuntimeError(
            f"Falta project_id para "
            f"{repository_key}"
        )

    try:
        return UUID(
            value
        )

    except ValueError as exc:
        raise RuntimeError(
            f"project_id inválido para "
            f"{repository_key}: {value}"
        ) from exc


def load_project_paths(
    *,
    db,
    project_id: UUID,
) -> set[str]:
    statement = (
        select(
            Document.path
        )
        .where(
            Document.project_id
            == project_id
        )
    )

    return {
        normalize_path(
            path
        )
        for path in db.scalars(
            statement
        ).all()
    }


def preflight_repository(
    *,
    db,
    repository_key: str,
    project_id: UUID,
    dataset_path: Path,
) -> None:
    expected_files = (
        load_expected_files(
            dataset_path
        )
    )

    project_paths = (
        load_project_paths(
            db=db,
            project_id=project_id,
        )
    )

    if not project_paths:
        raise RuntimeError(
            f"{repository_key}: "
            "el proyecto no contiene documentos. "
            "Debe estar indexado antes de ejecutar "
            "la validación."
        )

    missing = sorted(
        expected_files
        - project_paths
    )

    if missing:
        formatted = "\n".join(
            f"  - {path}"
            for path in missing
        )

        raise RuntimeError(
            f"{repository_key}: faltan "
            f"{len(missing)} archivos esperados "
            "en el proyecto indexado:\n"
            f"{formatted}"
        )

    print(
        f"[OK] {repository_key:<12} "
        f"documents={len(project_paths):>5} "
        f"expected={len(expected_files):>2} "
        "missing=0"
    )


def print_repository_summary(
    repository_key: str,
    report: EvaluationReport,
) -> None:
    summary = report.summary

    print()
    print("-" * 100)

    print(
        f"REPOSITORY: {repository_key}"
    )

    print("-" * 100)

    print(
        f"Cases:               "
        f"{len(report.results)}"
    )

    print(
        f"Hit@1:               "
        f"{summary.hit_at_1:.2%}"
    )

    print(
        f"Hit@3:               "
        f"{summary.hit_at_3:.2%}"
    )

    print(
        f"Hit@5:               "
        f"{summary.hit_at_5:.2%}"
    )

    print(
        f"Recall@5:            "
        f"{summary.recall_at_5:.2%}"
    )

    print(
        f"MRR:                 "
        f"{summary.mean_reciprocal_rank:.3f}"
    )

    print(
        f"Avg latency:         "
        f"{summary.average_latency_ms:.2f} ms"
    )


def main() -> None:
    suite = load_json(
        SUITE_PATH
    )

    mappings_payload = load_json(
        PROJECTS_PATH
    )

    repositories = suite.get(
        "repositories"
    )

    mappings = mappings_payload.get(
        "projects"
    )

    if not isinstance(
        repositories,
        list,
    ):
        raise RuntimeError(
            "suite.json no contiene repositories"
        )

    if not isinstance(
        mappings,
        dict,
    ):
        raise RuntimeError(
            "El mapping local no contiene projects"
        )

    if len(
        repositories
    ) != 3:
        raise RuntimeError(
            "La validación independiente debe "
            "contener exactamente 3 repositorios"
        )

    print()
    print("=" * 100)

    print(
        "DEVPILOT AI - RETRIEVAL V3 "
        "INDEPENDENT VALIDATION"
    )

    print("=" * 100)

    print()
    print(
        "FROZEN ONE-SHOT VALIDATION"
    )

    print()
    print(
        "No modificar Retrieval v3 ni este benchmark "
        "después de inspeccionar los resultados."
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

    print()
    print("=" * 100)

    print(
        "PREFLIGHT"
    )

    print("=" * 100)

    prepared: list[
        tuple[
            str,
            UUID,
            Path,
        ]
    ] = []

    for repository in repositories:
        if not isinstance(
            repository,
            dict,
        ):
            raise RuntimeError(
                "Entrada de repositorio inválida"
            )

        key = repository.get(
            "key"
        )

        dataset_value = (
            repository.get(
                "dataset"
            )
        )

        commit = repository.get(
            "commit"
        )

        if (
            not isinstance(
                key,
                str,
            )
            or not key.strip()
        ):
            raise RuntimeError(
                "Repository key inválido"
            )

        if (
            not isinstance(
                dataset_value,
                str,
            )
            or not dataset_value.strip()
        ):
            raise RuntimeError(
                f"{key}: dataset inválido"
            )

        if (
            not isinstance(
                commit,
                str,
            )
            or len(
                commit
            ) != 40
        ):
            raise RuntimeError(
                f"{key}: commit SHA inválido"
            )

        dataset_path = (
            BACKEND_ROOT
            / dataset_value
        ).resolve()

        project_id = get_project_id(
            mappings,
            key,
        )

        db = SessionLocal()

        try:
            preflight_repository(
                db=db,
                repository_key=key,
                project_id=project_id,
                dataset_path=dataset_path,
            )

        finally:
            db.close()

        prepared.append(
            (
                key,
                project_id,
                dataset_path,
            )
        )

    print()
    print(
        "[OK] Independent validation preflight complete."
    )

    print()
    print("=" * 100)

    print(
        "STARTING ONE-SHOT EVALUATION"
    )

    print("=" * 100)

    reports: list[
        tuple[
            str,
            EvaluationReport,
        ]
    ] = []

    for (
        repository_key,
        project_id,
        dataset_path,
    ) in prepared:
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

        finally:
            db.close()

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

    all_results = [
        result
        for _, report in reports
        for result in report.results
    ]

    total = len(
        all_results
    )

    if total != 30:
        raise RuntimeError(
            "Expected 30 validation cases, "
            f"found {total}"
        )

    hit_at_1 = sum(
        result.hit_at_1
        for result in all_results
    ) / total

    hit_at_3 = sum(
        result.hit_at_3
        for result in all_results
    ) / total

    hit_at_5 = sum(
        result.hit_at_5
        for result in all_results
    ) / total

    recall_at_5 = sum(
        result.recall_at_5
        for result in all_results
    ) / total

    mrr = sum(
        result.reciprocal_rank
        for result in all_results
    ) / total

    average_latency = sum(
        result.latency_ms
        for result in all_results
    ) / total

    failures = [
        result
        for result in all_results
        if result.hit_at_5 == 0
    ]

    print()
    print()
    print("=" * 100)

    print(
        "RETRIEVAL V3 INDEPENDENT "
        "VALIDATION SUMMARY"
    )

    print("=" * 100)

    print()
    print(
        f"Cases:                         "
        f"{total}"
    )

    print()
    print(
        "Retrieval quality"
    )

    print("-" * 100)

    print(
        f"Hit@1:                         "
        f"{hit_at_1:.2%}"
    )

    print(
        f"Hit@3:                         "
        f"{hit_at_3:.2%}"
    )

    print(
        f"Hit@5:                         "
        f"{hit_at_5:.2%}"
    )

    print(
        f"Recall@5:                      "
        f"{recall_at_5:.2%}"
    )

    print(
        f"MRR:                           "
        f"{mrr:.3f}"
    )

    print()
    print(
        "Performance"
    )

    print("-" * 100)

    print(
        f"Avg pipeline latency:          "
        f"{average_latency:.2f} ms"
    )

    print()
    print(
        "Independent validation failures"
    )

    print("-" * 100)

    print(
        f"Failures: {len(failures)}"
    )

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

        for rank, path in enumerate(
            result.retrieved_files,
            start=1,
        ):
            print(
                f"  {rank}. {path}"
            )

    print()
    print("=" * 100)

    print(
        "VALIDATION COMPLETE"
    )

    print("=" * 100)

    print()
    print(
        "These results are independent validation "
        "results for the frozen Retrieval v3 configuration."
    )

    print(
        "Do not tune Retrieval v3 using these results "
        "and continue calling this dataset independent."
    )


if __name__ == "__main__":
    main()