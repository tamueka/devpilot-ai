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
from evals.hybrid_retrieval import (
    DEFAULT_LEXICAL_CANDIDATE_K,
    DEFAULT_RRF_K,
    DEFAULT_VECTOR_CANDIDATE_K,
    build_hybrid_retriever,
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
    print("HYBRID RRF TOP 5")
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
    vector_candidate_k: int,
    lexical_candidate_k: int,
    rrf_k: int,
    dataset_path: Path | None,
) -> None:
    summary = report.summary

    print()
    print()
    print("=" * 100)
    print(
        "DEVPILOT AI - "
        "HYBRID RETRIEVAL + RRF"
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
    print("Hybrid configuration")
    print("-" * 100)

    print(
        f"Vector candidates:       "
        f"{vector_candidate_k}"
    )

    print(
        f"Lexical candidates:      "
        f"{lexical_candidate_k}"
    )

    print(
        f"RRF k:                   "
        f"{rrf_k}"
    )

    print(
        f"Final documents:         "
        f"{FINAL_K}"
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
    vector_candidate_k: int,
    lexical_candidate_k: int,
    rrf_k: int,
    dataset_path: Path | None,
) -> None:
    db = SessionLocal()

    try:
        retrieve = build_hybrid_retriever(
            db=db,
            project_id=project_id,
            vector_candidate_k=vector_candidate_k,
            lexical_candidate_k=lexical_candidate_k,
            rrf_k=rrf_k,
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
            vector_candidate_k=vector_candidate_k,
            lexical_candidate_k=lexical_candidate_k,
            rrf_k=rrf_k,
            dataset_path=dataset_path,
        )

    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Ejecuta la evaluación híbrida de "
            "DevPilot AI combinando vector y "
            "PostgreSQL FTS mediante RRF."
        )
    )

    parser.add_argument(
        "--project-id",
        required=True,
        type=parse_project_id,
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

    parser.add_argument(
        "--vector-candidate-k",
        type=int,
        default=DEFAULT_VECTOR_CANDIDATE_K,
    )

    parser.add_argument(
        "--lexical-candidate-k",
        type=int,
        default=DEFAULT_LEXICAL_CANDIDATE_K,
    )

    parser.add_argument(
        "--rrf-k",
        type=int,
        default=DEFAULT_RRF_K,
    )

    args = parser.parse_args()

    if args.vector_candidate_k <= 0:
        parser.error(
            "--vector-candidate-k debe ser mayor que cero"
        )

    if args.lexical_candidate_k <= 0:
        parser.error(
            "--lexical-candidate-k debe ser mayor que cero"
        )

    if args.rrf_k <= 0:
        parser.error(
            "--rrf-k debe ser mayor que cero"
        )

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
        vector_candidate_k=args.vector_candidate_k,
        lexical_candidate_k=args.lexical_candidate_k,
        rrf_k=args.rrf_k,
        dataset_path=args.dataset,
    )


if __name__ == "__main__":
    main()