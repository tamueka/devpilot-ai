from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from app.db.database import SessionLocal
from evals.evaluator import (
    EvaluationCase,
    load_dataset,
)
from evals.lexical_retrieval import (
    build_lexical_retriever,
)
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


@dataclass(frozen=True)
class CandidateCaseResult:
    case_id: str

    vector_recall: float
    lexical_recall: float
    union_recall: float

    vector_full_coverage: bool
    lexical_full_coverage: bool
    union_full_coverage: bool

    vector_candidate_count: int
    lexical_candidate_count: int
    union_candidate_count: int


def parse_project_id(
    value: str,
) -> UUID:
    try:
        return UUID(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Project ID inválido: {value}"
        ) from exc


def merge_unique_paths(
    *path_groups: list[str],
) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()

    for paths in path_groups:
        for path in paths:
            normalized = normalize_path(
                path
            )

            if normalized in seen:
                continue

            seen.add(
                normalized
            )

            merged.append(
                path
            )

    return merged


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

    relevant = expected.intersection(
        retrieved
    )

    return (
        len(relevant)
        / len(expected)
    )


def find_expected_ranks(
    retrieved_files: list[str],
    expected_files: tuple[str, ...],
) -> dict[str, int | None]:
    normalized_positions = {
        normalize_path(path): position
        for position, path in enumerate(
            retrieved_files,
            start=1,
        )
    }

    return {
        expected: normalized_positions.get(
            normalize_path(
                expected
            )
        )
        for expected in expected_files
    }


def print_candidate_ranking(
    title: str,
    retrieved_files: list[str],
    expected_files: tuple[str, ...],
) -> None:
    expected = {
        normalize_path(path)
        for path in expected_files
    }

    print()
    print(title)
    print("-" * 100)

    if not retrieved_files:
        print(
            "  Sin candidatos"
        )
        return

    for position, path in enumerate(
        retrieved_files,
        start=1,
    ):
        marker = (
            "✓"
            if normalize_path(path)
            in expected
            else " "
        )

        print(
            f"{marker} "
            f"{position:>2}. "
            f"{path}"
        )


def evaluate_case(
    case: EvaluationCase,
    vector_retrieve,
    lexical_retrieve,
) -> CandidateCaseResult:
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

    union_files = merge_unique_paths(
        vector_files,
        lexical_files,
    )

    vector_recall = candidate_recall(
        vector_files,
        case.expected_files,
    )

    lexical_recall = candidate_recall(
        lexical_files,
        case.expected_files,
    )

    union_recall = candidate_recall(
        union_files,
        case.expected_files,
    )

    print()
    print("=" * 100)

    print(
        f"{case.id} | "
        f"{case.category}"
    )

    print("=" * 100)

    print(
        f"Pregunta: "
        f"{case.question}"
    )

    print()
    print("Esperado:")

    for expected_file in case.expected_files:
        print(
            f"  - {expected_file}"
        )

    print_candidate_ranking(
        title="VECTOR CANDIDATES",
        retrieved_files=vector_files,
        expected_files=case.expected_files,
    )

    print_candidate_ranking(
        title="LEXICAL CANDIDATES",
        retrieved_files=lexical_files,
        expected_files=case.expected_files,
    )

    vector_ranks = find_expected_ranks(
        vector_files,
        case.expected_files,
    )

    lexical_ranks = find_expected_ranks(
        lexical_files,
        case.expected_files,
    )

    print()
    print("Expected ranks")
    print("-" * 100)

    for expected_file in case.expected_files:
        print(
            expected_file
        )

        print(
            f"  Vector:  "
            f"{vector_ranks[expected_file]}"
        )

        print(
            f"  Lexical: "
            f"{lexical_ranks[expected_file]}"
        )

    print()
    print(
        f"Vector candidate recall:  "
        f"{vector_recall:.2%}"
    )

    print(
        f"Lexical candidate recall: "
        f"{lexical_recall:.2%}"
    )

    print(
        f"Union candidate recall:   "
        f"{union_recall:.2%}"
    )

    print()
    print(
        f"Vector candidates:  "
        f"{len(vector_files)}"
    )

    print(
        f"Lexical candidates: "
        f"{len(lexical_files)}"
    )

    print(
        f"Union candidates:   "
        f"{len(union_files)}"
    )

    return CandidateCaseResult(
        case_id=case.id,
        vector_recall=vector_recall,
        lexical_recall=lexical_recall,
        union_recall=union_recall,
        vector_full_coverage=(
            vector_recall == 1.0
        ),
        lexical_full_coverage=(
            lexical_recall == 1.0
        ),
        union_full_coverage=(
            union_recall == 1.0
        ),
        vector_candidate_count=len(
            vector_files
        ),
        lexical_candidate_count=len(
            lexical_files
        ),
        union_candidate_count=len(
            union_files
        ),
    )


def print_summary(
    results: list[CandidateCaseResult],
    *,
    dataset_name: str,
    dataset_version: str,
    dataset_path: Path | None,
) -> None:
    total = len(
        results
    )

    vector_recall = mean_metric(
        [
            result.vector_recall
            for result in results
        ]
    )

    lexical_recall = mean_metric(
        [
            result.lexical_recall
            for result in results
        ]
    )

    union_recall = mean_metric(
        [
            result.union_recall
            for result in results
        ]
    )

    vector_full = sum(
        result.vector_full_coverage
        for result in results
    )

    lexical_full = sum(
        result.lexical_full_coverage
        for result in results
    )

    union_full = sum(
        result.union_full_coverage
        for result in results
    )

    average_vector_candidates = mean_metric(
        [
            float(
                result.vector_candidate_count
            )
            for result in results
        ]
    )

    average_lexical_candidates = mean_metric(
        [
            float(
                result.lexical_candidate_count
            )
            for result in results
        ]
    )

    average_union_candidates = mean_metric(
        [
            float(
                result.union_candidate_count
            )
            for result in results
        ]
    )

    print()
    print()
    print("=" * 100)
    print(
        "DEVPILOT AI - CANDIDATE RECALL"
    )
    print("=" * 100)

    print(
        f"Dataset:                      "
        f"{dataset_name}"
    )

    print(
        f"Dataset version:              "
        f"{dataset_version}"
    )

    print(
        f"Dataset file:                 "
        f"{dataset_path if dataset_path else 'default'}"
    )

    print(
        f"Cases:                        "
        f"{total}"
    )

    print()
    print("Candidate configuration")
    print("-" * 100)

    print(
        f"Vector chunk oversampling:    "
        f"{DEFAULT_CHUNK_CANDIDATE_K}"
    )

    print(
        f"Vector document candidates:   "
        f"{VECTOR_DOCUMENT_K}"
    )

    print(
        f"Lexical document candidates:  "
        f"{LEXICAL_DOCUMENT_K}"
    )

    print()
    print("Average candidate recall")
    print("-" * 100)

    print(
        f"Vector Recall@20:              "
        f"{vector_recall:.2%}"
    )

    print(
        f"Lexical Recall@20:             "
        f"{lexical_recall:.2%}"
    )

    print(
        f"Union candidate recall:        "
        f"{union_recall:.2%}"
    )

    print()
    print("Full expected coverage")
    print("-" * 100)

    print(
        f"Vector:                        "
        f"{vector_full}/{total} "
        f"({vector_full / total:.2%})"
    )

    print(
        f"Lexical:                       "
        f"{lexical_full}/{total} "
        f"({lexical_full / total:.2%})"
    )

    print(
        f"Union:                         "
        f"{union_full}/{total} "
        f"({union_full / total:.2%})"
    )

    print()
    print("Average candidate pool size")
    print("-" * 100)

    print(
        f"Vector:                        "
        f"{average_vector_candidates:.2f}"
    )

    print(
        f"Lexical:                       "
        f"{average_lexical_candidates:.2f}"
    )

    print(
        f"Union:                         "
        f"{average_union_candidates:.2f}"
    )

    failed_union_cases = [
        result.case_id
        for result in results
        if not result.union_full_coverage
    ]

    print()
    print("Union failures")
    print("-" * 100)

    if not failed_union_cases:
        print(
            "Ninguno"
        )
    else:
        for case_id in failed_union_cases:
            print(
                f"  - {case_id}"
            )


def run(
    *,
    project_id: UUID,
    dataset_path: Path | None,
) -> None:
    db = SessionLocal()

    try:
        (
            dataset_name,
            dataset_version,
            cases,
        ) = load_dataset(
            dataset_path=dataset_path,
        )

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
                candidate_k=(
                    LEXICAL_DOCUMENT_K
                ),
            )
        )

        results = [
            evaluate_case(
                case=case,
                vector_retrieve=vector_retrieve,
                lexical_retrieve=lexical_retrieve,
            )
            for case in cases
        ]

        print_summary(
            results=results,
            dataset_name=dataset_name,
            dataset_version=dataset_version,
            dataset_path=dataset_path,
        )

    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Evalúa la cobertura del pool "
            "Vector + Lexical antes del reranking."
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