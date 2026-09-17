from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from uuid import UUID

from app.db.database import SessionLocal
from evals.evaluator import load_dataset
from evals.hybrid_retrieval import reciprocal_rank_fusion
from evals.lexical_retrieval import build_lexical_retriever
from evals.retrieval_metrics import (
    mean_metric,
    normalize_path,
)
from evals.vector_candidate_retrieval import (
    DEFAULT_CHUNK_CANDIDATE_K,
    build_vector_candidate_retriever,
)


VECTOR_DOCUMENT_K = 20
LEXICAL_DOCUMENT_K = 20
RRF_K = 60

VECTOR_WEIGHT = 1.0
LEXICAL_WEIGHT = 1.0

CUTOFFS = (
    5,
    10,
    15,
    20,
)


@dataclass
class CutoffMetrics:
    recalls: list[float] = field(
        default_factory=list
    )
    full_coverage_cases: list[str] = field(
        default_factory=list
    )
    failed_cases: list[str] = field(
        default_factory=list
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


def candidate_recall(
    retrieved_files: list[str],
    expected_files: tuple[str, ...],
) -> float:
    expected = {
        normalize_path(path)
        for path in expected_files
    }

    if not expected:
        return 0.0

    retrieved = {
        normalize_path(path)
        for path in retrieved_files
    }

    return (
        len(
            expected.intersection(
                retrieved
            )
        )
        / len(expected)
    )


def run(
    project_id: UUID,
) -> None:
    db = SessionLocal()

    try:
        (
            dataset_name,
            dataset_version,
            cases,
        ) = load_dataset()

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
                candidate_k=LEXICAL_DOCUMENT_K,
            )
        )

        metrics = {
            cutoff: CutoffMetrics()
            for cutoff in CUTOFFS
        }

        print()
        print("=" * 100)
        print(
            "DEVPILOT AI - RRF CANDIDATE CUTOFF"
        )
        print("=" * 100)

        print(
            f"Dataset: {dataset_name}"
        )
        print(
            f"Version: {dataset_version}"
        )
        print(
            f"Cases:   {len(cases)}"
        )

        print()
        print(
            f"Vector documents:  "
            f"{VECTOR_DOCUMENT_K}"
        )
        print(
            f"Lexical documents: "
            f"{LEXICAL_DOCUMENT_K}"
        )
        print(
            f"Vector chunks:      "
            f"{DEFAULT_CHUNK_CANDIDATE_K}"
        )
        print(
            f"RRF k:              "
            f"{RRF_K}"
        )

        print()

        for index, case in enumerate(
            cases,
            start=1,
        ):
            print(
                f"[{index}/{len(cases)}] "
                f"{case.id}"
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

            fused_results = reciprocal_rank_fusion(
                vector_files=vector_files,
                lexical_files=lexical_files,
                final_k=(
                    VECTOR_DOCUMENT_K
                    + LEXICAL_DOCUMENT_K
                ),
                rrf_k=RRF_K,
                vector_weight=VECTOR_WEIGHT,
                lexical_weight=LEXICAL_WEIGHT,
            )

            fused_files = [
                result.path
                for result in fused_results
            ]

            for cutoff in CUTOFFS:
                retrieved = fused_files[
                    :cutoff
                ]

                recall = candidate_recall(
                    retrieved,
                    case.expected_files,
                )

                current = metrics[
                    cutoff
                ]

                current.recalls.append(
                    recall
                )

                if recall == 1.0:
                    current.full_coverage_cases.append(
                        case.id
                    )
                else:
                    current.failed_cases.append(
                        case.id
                    )

        print()
        print()
        print("=" * 100)
        print(
            "RRF CUTOFF COMPARISON"
        )
        print("=" * 100)

        print(
            f"{'Cutoff':<12}"
            f"{'Recall':>14}"
            f"{'Full coverage':>20}"
            f"{'Failures':>14}"
        )

        print(
            "-" * 100
        )

        for cutoff in CUTOFFS:
            current = metrics[
                cutoff
            ]

            recall = mean_metric(
                current.recalls
            )

            full_coverage = len(
                current.full_coverage_cases
            )

            failures = len(
                current.failed_cases
            )

            print(
                f"Top {cutoff:<7}"
                f"{recall:>13.2%}"
                f"{full_coverage:>14}"
                f"/{len(cases):<5}"
                f"{failures:>12}"
            )

        print()
        print("=" * 100)
        print(
            "FAILED CASES"
        )
        print("=" * 100)

        for cutoff in CUTOFFS:
            current = metrics[
                cutoff
            ]

            failures = (
                ", ".join(
                    current.failed_cases
                )
                if current.failed_cases
                else "Ninguno"
            )

            print(
                f"Top {cutoff:<3}: "
                f"{failures}"
            )

        print()
        print(
            "Objetivo: encontrar el menor cutoff "
            "que mantenga cobertura completa o "
            "prácticamente completa antes del reranker."
        )

    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Evalúa cuánto puede reducirse el pool "
            "RRF antes del reranking."
        )
    )

    parser.add_argument(
        "--project-id",
        required=True,
        type=parse_project_id,
    )

    args = parser.parse_args()

    run(
        project_id=args.project_id,
    )


if __name__ == "__main__":
    main()