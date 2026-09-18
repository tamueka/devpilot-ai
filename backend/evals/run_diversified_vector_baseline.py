from __future__ import annotations

import argparse
from uuid import UUID

from app.db.database import SessionLocal
from evals.diversified_vector_retrieval import (
    DEFAULT_CANDIDATE_K,
    build_diversified_vector_retriever,
)
from evals.evaluator import (
    CaseEvaluationResult,
    EvaluationReport,
    evaluate_dataset,
)


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
    print("=" * 80)
    print(
        f"[{index}/{total}] "
        f"{result.case_id} | "
        f"{result.category}"
    )
    print("=" * 80)

    print(
        f"Pregunta: {result.question}"
    )

    print()
    print("Archivos esperados:")

    for path in result.expected_files:
        print(
            f"  - {path}"
        )

    print()
    print("Archivos recuperados:")

    if not result.retrieved_files:
        print(
            "  - Ningún resultado"
        )
    else:
        for position, path in enumerate(
            result.retrieved_files,
            start=1,
        ):
            print(
                f"  {position}. {path}"
            )

    print()
    print(
        f"Hit@1:         "
        f"{result.hit_at_1:.0f}"
    )
    print(
        f"Hit@3:         "
        f"{result.hit_at_3:.0f}"
    )
    print(
        f"Hit@5:         "
        f"{result.hit_at_5:.0f}"
    )
    print(
        f"Recall@5:      "
        f"{result.recall_at_5:.3f}"
    )
    print(
        f"RR:            "
        f"{result.reciprocal_rank:.3f}"
    )

    print()
    print(
        f"Unique docs@5: "
        f"{result.unique_documents_at_5}"
    )
    print(
        f"Docs ratio@5:  "
        f"{result.documentation_ratio_at_5:.2%}"
    )
    print(
        f"Code ratio@5:  "
        f"{result.code_ratio_at_5:.2%}"
    )

    print()
    print(
        f"Latency:       "
        f"{result.latency_ms:.2f} ms"
    )


def print_summary(
    report: EvaluationReport,
    candidate_k: int,
) -> None:
    summary = report.summary

    print()
    print()
    print("=" * 80)
    print(
        "DEVPILOT AI - "
        "DIVERSIFIED VECTOR RETRIEVAL"
    )
    print("=" * 80)

    print(
        f"Dataset:              "
        f"{report.dataset_name}"
    )

    print(
        f"Dataset version:      "
        f"{report.dataset_version}"
    )

    print(
        f"Cases:                "
        f"{summary.total_cases}"
    )

    print(
        f"Candidate chunks:     "
        f"{candidate_k}"
    )

    print(
        "Final documents:      5"
    )

    print()
    print(
        "Retrieval quality"
    )
    print("-" * 80)

    print(
        f"Hit@1:                "
        f"{summary.hit_at_1:.2%}"
    )

    print(
        f"Hit@3:                "
        f"{summary.hit_at_3:.2%}"
    )

    print(
        f"Hit@5:                "
        f"{summary.hit_at_5:.2%}"
    )

    print(
        f"Recall@5:             "
        f"{summary.recall_at_5:.2%}"
    )

    print(
        f"MRR:                  "
        f"{summary.mrr:.3f}"
    )

    print()
    print(
        "Retrieval diagnostics"
    )
    print("-" * 80)

    print(
        f"Unique docs@5:        "
        f"{summary.average_unique_documents_at_5:.2f}"
    )

    print(
        f"Documentation ratio:  "
        f"{summary.average_documentation_ratio_at_5:.2%}"
    )

    print(
        f"Code ratio:           "
        f"{summary.average_code_ratio_at_5:.2%}"
    )

    print()
    print(
        "Performance"
    )
    print("-" * 80)

    print(
        f"Avg retrieval latency:"
        f" {summary.average_latency_ms:.2f} ms"
    )

    print()
    print(
        "Nota: se recuperan primero chunks candidatos mediante "
        "búsqueda vectorial y posteriormente se eliminan paths "
        "duplicados conservando el ranking original."
    )

    print(
        "La latencia incluye generación del embedding, búsqueda "
        "pgvector y diversificación por documento."
    )


def run(
    project_id: UUID,
    candidate_k: int,
) -> None:
    db = SessionLocal()

    try:
        retrieve = (
            build_diversified_vector_retriever(
                db=db,
                project_id=project_id,
                candidate_k=candidate_k,
            )
        )

        report = evaluate_dataset(
            retrieve=retrieve,
            retrieval_k=5,
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
            candidate_k=candidate_k,
        )

    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Evalúa el retrieval vectorial de DevPilot AI "
            "aplicando diversificación por documento."
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
        "--candidate-k",
        type=int,
        default=DEFAULT_CANDIDATE_K,
        help=(
            "Número de chunks vectoriales candidatos "
            "antes de eliminar documentos duplicados. "
            f"Por defecto: {DEFAULT_CANDIDATE_K}."
        ),
    )

    args = parser.parse_args()

    if args.candidate_k <= 0:
        parser.error(
            "--candidate-k debe ser mayor que cero"
        )

    run(
        project_id=args.project_id,
        candidate_k=args.candidate_k,
    )


if __name__ == "__main__":
    main()