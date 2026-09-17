from __future__ import annotations

import argparse
from pathlib import Path
from uuid import UUID

from app.db.database import SessionLocal
from evals.evaluator import (
    CaseEvaluationResult,
    EvaluationReport,
    evaluate_dataset,
)
from evals.vector_retrieval import (
    build_vector_retriever,
)


FINAL_K = 5


def parse_project_id(
    value: str,
) -> UUID:
    try:
        return UUID(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Project ID inválido: {value}"
        ) from exc


def print_case_result(
    index: int,
    total: int,
    result: CaseEvaluationResult,
) -> None:
    print()
    print("=" * 100)

    print(
        f"[{index}/{total}] "
        f"{result.case_id} | "
        f"{result.category}"
    )

    print("=" * 100)

    print(
        f"Pregunta: {result.question}"
    )

    print()
    print("Esperado:")

    for path in result.expected_files:
        print(
            f"  - {path}"
        )

    print()
    print("VECTOR TOP 5")
    print("-" * 100)

    expected_files = set(
        result.expected_files
    )

    for position, path in enumerate(
        result.retrieved_files,
        start=1,
    ):
        marker = (
            "✓"
            if path in expected_files
            else " "
        )

        print(
            f"{marker} "
            f"{position}. {path}"
        )

    print()
    print(
        f"Hit@1:    "
        f"{result.hit_at_1:.0f}"
    )

    print(
        f"Hit@3:    "
        f"{result.hit_at_3:.0f}"
    )

    print(
        f"Hit@5:    "
        f"{result.hit_at_5:.0f}"
    )

    print(
        f"Recall@5: "
        f"{result.recall_at_5:.3f}"
    )

    print(
        f"RR:       "
        f"{result.reciprocal_rank:.3f}"
    )

    print()
    print(
        f"Latency:  "
        f"{result.latency_ms:.2f} ms"
    )


def print_summary(
    report: EvaluationReport,
    *,
    dataset_path: Path | None,
) -> None:
    summary = report.summary

    print()
    print()
    print("=" * 100)
    print(
        "DEVPILOT AI - VECTOR BASELINE"
    )
    print("=" * 100)

    print(
        f"Dataset:                 "
        f"{report.dataset_name}"
    )

    print(
        f"Dataset version:         "
        f"{report.dataset_version}"
    )

    print(
        f"Dataset file:            "
        f"{dataset_path if dataset_path else 'default'}"
    )

    print(
        f"Cases:                   "
        f"{summary.total_cases}"
    )

    print()
    print("Retrieval quality")
    print("-" * 100)

    print(
        f"Hit@1:                   "
        f"{summary.hit_at_1:.2%}"
    )

    print(
        f"Hit@3:                   "
        f"{summary.hit_at_3:.2%}"
    )

    print(
        f"Hit@5:                   "
        f"{summary.hit_at_5:.2%}"
    )

    print(
        f"Recall@5:                "
        f"{summary.recall_at_5:.2%}"
    )

    print(
        f"MRR:                     "
        f"{summary.mrr:.3f}"
    )

    print()
    print("Diagnostics")
    print("-" * 100)

    print(
        f"Unique docs@5:           "
        f"{summary.average_unique_documents_at_5:.2f}"
    )

    print(
        f"Documentation ratio:     "
        f"{summary.average_documentation_ratio_at_5:.2%}"
    )

    print(
        f"Code ratio:              "
        f"{summary.average_code_ratio_at_5:.2%}"
    )

    print()
    print("Performance")
    print("-" * 100)

    print(
        f"Avg retrieval latency:   "
        f"{summary.average_latency_ms:.2f} ms"
    )


def run(
    *,
    project_id: UUID,
    dataset_path: Path | None,
) -> None:
    db = SessionLocal()

    try:
        retrieve = build_vector_retriever(
            db=db,
            project_id=project_id,
        )

        report = evaluate_dataset(
            retrieve=retrieve,
            retrieval_k=FINAL_K,
            dataset_path=dataset_path,
        )

        total = len(
            report.results
        )

        for index, result in enumerate(
            report.results,
            start=1,
        ):
            print_case_result(
                index=index,
                total=total,
                result=result,
            )

        print_summary(
            report=report,
            dataset_path=dataset_path,
        )

    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Ejecuta el baseline vectorial "
            "de DevPilot AI."
        )
    )

    parser.add_argument(
        "--project-id",
        required=True,
        type=parse_project_id,
        help=(
            "UUID del proyecto previamente indexado."
        ),
    )

    parser.add_argument(
        "--dataset",
        type=Path,
        default=None,
        help=(
            "Ruta al dataset JSON. "
            "Si no se especifica se utiliza "
            "evals/datasets/rag_eval.json."
        ),
    )

    args = parser.parse_args()

    if (
        args.dataset is not None
        and not args.dataset.exists()
    ):
        parser.error(
            f"El dataset no existe: "
            f"{args.dataset}"
        )

    run(
        project_id=args.project_id,
        dataset_path=args.dataset,
    )


if __name__ == "__main__":
    main()