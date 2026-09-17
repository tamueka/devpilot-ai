from __future__ import annotations

import argparse
from uuid import UUID

from app.db.database import SessionLocal
from evals.diversified_vector_retrieval import (
    build_diversified_vector_retriever,
)
from evals.evaluator import load_dataset
from evals.hybrid_retrieval import reciprocal_rank_fusion
from evals.lexical_retrieval import build_lexical_retriever
from evals.retrieval_metrics import normalize_path


VECTOR_CANDIDATE_K = 20
LEXICAL_CANDIDATE_K = 20
RRF_K = 60

VECTOR_WEIGHT = 1.0
LEXICAL_WEIGHT = 1.5

FAILURE_CASES = {
    "retrieval-001",
    "tests-001",
}


def parse_project_id(value: str) -> UUID:
    try:
        return UUID(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Project ID inválido: {value}"
        ) from exc


def find_rank(
    paths: list[str],
    expected_files: tuple[str, ...],
) -> int | None:
    expected = {
        normalize_path(path)
        for path in expected_files
    }

    for rank, path in enumerate(
        paths,
        start=1,
    ):
        if normalize_path(path) in expected:
            return rank

    return None


def print_ranking(
    title: str,
    paths: list[str],
    expected_files: tuple[str, ...],
) -> None:
    expected = {
        normalize_path(path)
        for path in expected_files
    }

    print()
    print(title)
    print("-" * 100)

    for rank, path in enumerate(
        paths,
        start=1,
    ):
        marker = (
            "✓"
            if normalize_path(path) in expected
            else " "
        )

        print(
            f"{marker} {rank:>2}. {path}"
        )


def run(project_id: UUID) -> None:
    db = SessionLocal()

    try:
        _, _, cases = load_dataset()

        vector_retrieve = (
            build_diversified_vector_retriever(
                db=db,
                project_id=project_id,
                candidate_k=VECTOR_CANDIDATE_K,
            )
        )

        lexical_retrieve = (
            build_lexical_retriever(
                db=db,
                project_id=project_id,
                candidate_k=LEXICAL_CANDIDATE_K,
            )
        )

        for case in cases:
            if case.id not in FAILURE_CASES:
                continue

            vector_files = list(
                vector_retrieve(
                    case.question,
                    VECTOR_CANDIDATE_K,
                )
            )

            lexical_files = list(
                lexical_retrieve(
                    case.question,
                    LEXICAL_CANDIDATE_K,
                )
            )

            fused_results = reciprocal_rank_fusion(
                vector_files=vector_files,
                lexical_files=lexical_files,
                final_k=20,
                rrf_k=RRF_K,
                vector_weight=VECTOR_WEIGHT,
                lexical_weight=LEXICAL_WEIGHT,
            )

            fused_files = [
                result.path
                for result in fused_results
            ]

            print()
            print("=" * 100)
            print(
                f"{case.id} | {case.question}"
            )
            print("=" * 100)

            print()
            print("Esperado:")

            for path in case.expected_files:
                print(f"  - {path}")

            print_ranking(
                "VECTOR",
                vector_files,
                case.expected_files,
            )

            print_ranking(
                "LEXICAL",
                lexical_files,
                case.expected_files,
            )

            print()
            print("WEIGHTED RRF")
            print("-" * 100)

            expected = {
                normalize_path(path)
                for path in case.expected_files
            }

            for rank, result in enumerate(
                fused_results,
                start=1,
            ):
                marker = (
                    "✓"
                    if normalize_path(result.path)
                    in expected
                    else " "
                )

                vector_rank = (
                    result.vector_rank
                    if result.vector_rank is not None
                    else "-"
                )

                lexical_rank = (
                    result.lexical_rank
                    if result.lexical_rank is not None
                    else "-"
                )

                print(
                    f"{marker} {rank:>2}. "
                    f"score={result.score:.6f} "
                    f"V={vector_rank!s:<3} "
                    f"L={lexical_rank!s:<3} "
                    f"{result.path}"
                )

            print()
            print("Expected document ranks")
            print("-" * 100)

            print(
                "Vector:  ",
                find_rank(
                    vector_files,
                    case.expected_files,
                ),
            )

            print(
                "Lexical: ",
                find_rank(
                    lexical_files,
                    case.expected_files,
                ),
            )

            print(
                "RRF:     ",
                find_rank(
                    fused_files,
                    case.expected_files,
                ),
            )

    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Inspecciona los casos que siguen fallando "
            "en Weighted RRF."
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