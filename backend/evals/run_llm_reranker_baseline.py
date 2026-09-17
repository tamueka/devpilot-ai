from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from pathlib import Path
from uuid import UUID

from app.db.database import SessionLocal
from evals.evaluator import (
    CaseEvaluationResult,
    EvaluationReport,
    evaluate_dataset,
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


FINAL_K = 5


RetrievalFunction = Callable[
    [str, int],
    Sequence[str],
]


def parse_project_id(
    value: str,
) -> UUID:
    try:
        return UUID(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Project ID inválido: {value}"
        ) from exc


def build_llm_reranked_retriever(
    *,
    db,
    project_id: UUID,
    model: str,
    candidate_k: int,
    max_chars_per_document: int,
) -> RetrievalFunction:
    """
    Pipeline completo:

        Vector retrieval
            +
        Lexical retrieval
            ↓
        RRF
            ↓
        Top N candidates
            ↓
        LLM reranker
            ↓
        Top K final
    """

    if candidate_k <= 0:
        raise ValueError(
            "candidate_k must be greater than zero"
        )

    if max_chars_per_document <= 0:
        raise ValueError(
            "max_chars_per_document must be greater than zero"
        )

    if not model.strip():
        raise ValueError(
            "model must not be blank"
        )

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
        if k <= 0:
            raise ValueError(
                "k must be greater than zero"
            )

        candidate_paths = list(
            candidate_retrieve(
                question,
                candidate_k,
            )
        )

        return rerank_candidate_paths(
            db=db,
            project_id=project_id,
            question=question,
            candidate_paths=candidate_paths,
            top_k=k,
            model=model,
            max_chars_per_document=(
                max_chars_per_document
            ),
        )

    return retrieve


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
    print("LLM RERANKER TOP 5")
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
    model: str,
    candidate_k: int,
    max_chars_per_document: int,
    dataset_path: Path | None,
) -> None:
    summary = report.summary

    print()
    print()
    print("=" * 100)

    print(
        "DEVPILOT AI - "
        "LLM RERANKER BASELINE"
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
    print("Configuration")
    print("-" * 100)

    print(
        f"Rerank model:            "
        f"{model}"
    )

    print(
        f"RRF candidates:          "
        f"{candidate_k}"
    )

    print(
        f"Final documents:         "
        f"{FINAL_K}"
    )

    print(
        f"Max chars/document:      "
        f"{max_chars_per_document}"
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
        f"Avg pipeline latency:    "
        f"{summary.average_latency_ms:.2f} ms"
    )

    print()
    print(
        "La latencia incluye candidate retrieval, "
        "RRF, carga de contenido y llamada al reranker."
    )


def run(
    *,
    project_id: UUID,
    model: str,
    candidate_k: int,
    max_chars_per_document: int,
    dataset_path: Path | None,
) -> None:
    db = SessionLocal()

    try:
        retrieve = build_llm_reranked_retriever(
            db=db,
            project_id=project_id,
            model=model,
            candidate_k=candidate_k,
            max_chars_per_document=(
                max_chars_per_document
            ),
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
            model=model,
            candidate_k=candidate_k,
            max_chars_per_document=(
                max_chars_per_document
            ),
            dataset_path=dataset_path,
        )

    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Evalúa DevPilot AI utilizando "
            "Hybrid Retrieval + RRF + LLM reranking."
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
            "Ruta al dataset JSON de evaluación. "
            "Si no se especifica se utiliza "
            "evals/datasets/rag_eval.json."
        ),
    )

    parser.add_argument(
        "--model",
        default=DEFAULT_RERANK_MODEL,
        help=(
            "Modelo utilizado por el reranker."
        ),
    )

    parser.add_argument(
        "--candidate-k",
        type=int,
        default=DEFAULT_RERANK_CANDIDATE_K,
        help=(
            "Número de candidatos RRF enviados "
            "al reranker. Por defecto: 10."
        ),
    )

    parser.add_argument(
        "--max-chars-per-document",
        type=int,
        default=DEFAULT_MAX_CHARS_PER_DOCUMENT,
        help=(
            "Máximo de caracteres de contenido "
            "por documento candidato."
        ),
    )

    args = parser.parse_args()

    if args.candidate_k <= 0:
        parser.error(
            "--candidate-k debe ser mayor que cero"
        )

    if args.max_chars_per_document <= 0:
        parser.error(
            "--max-chars-per-document debe ser mayor que cero"
        )

    if not args.model.strip():
        parser.error(
            "--model no puede estar vacío"
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
        model=args.model,
        candidate_k=args.candidate_k,
        max_chars_per_document=(
            args.max_chars_per_document
        ),
        dataset_path=args.dataset,
    )


if __name__ == "__main__":
    main()