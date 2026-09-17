from __future__ import annotations

import argparse
from time import perf_counter
from uuid import UUID

from app.db.database import SessionLocal
from evals.diversified_vector_retrieval import (
    build_diversified_vector_retriever,
)
from evals.evaluator import (
    EvaluationCase,
    load_dataset,
)
from evals.lexical_retrieval import (
    build_lexical_retriever,
)
from evals.retrieval_metrics import (
    hit_at_k,
    normalize_path,
)


TOP_K = 5
CANDIDATE_K = 20


def parse_project_id(
    value: str,
) -> UUID:
    try:
        return UUID(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Project ID inválido: {value}"
        ) from exc


def is_expected(
    path: str,
    expected_files: tuple[str, ...],
) -> bool:
    normalized_expected = {
        normalize_path(expected)
        for expected in expected_files
    }

    return (
        normalize_path(path)
        in normalized_expected
    )


def print_results(
    title: str,
    retrieved_files: list[str],
    expected_files: tuple[str, ...],
    latency_ms: float,
) -> None:
    print()
    print(title)
    print("-" * 80)

    if not retrieved_files:
        print("  Sin resultados")
    else:
        for position, path in enumerate(
            retrieved_files,
            start=1,
        ):
            marker = (
                "✓"
                if is_expected(
                    path,
                    expected_files,
                )
                else " "
            )

            print(
                f"{marker} "
                f"{position}. {path}"
            )

    hit = hit_at_k(
        retrieved_files,
        expected_files,
        TOP_K,
    )

    print()
    print(
        f"Hit@5:   {hit:.0f}"
    )
    print(
        f"Latency: {latency_ms:.2f} ms"
    )


def evaluate_case(
    case: EvaluationCase,
    vector_retrieve,
    lexical_retrieve,
) -> tuple[float, float]:
    print()
    print("=" * 80)
    print(
        f"{case.id} | {case.category}"
    )
    print("=" * 80)

    print(
        f"Pregunta: {case.question}"
    )

    print()
    print(
        "Esperado:"
    )

    for path in case.expected_files:
        print(
            f"  - {path}"
        )

    vector_start = perf_counter()

    vector_results = list(
        vector_retrieve(
            case.question,
            TOP_K,
        )
    )

    vector_latency = (
        perf_counter() - vector_start
    ) * 1000

    lexical_start = perf_counter()

    lexical_results = list(
        lexical_retrieve(
            case.question,
            TOP_K,
        )
    )

    lexical_latency = (
        perf_counter() - lexical_start
    ) * 1000

    print_results(
        title="VECTOR DIVERSIFICADO",
        retrieved_files=vector_results,
        expected_files=case.expected_files,
        latency_ms=vector_latency,
    )

    print_results(
        title="LEXICAL / POSTGRESQL FTS",
        retrieved_files=lexical_results,
        expected_files=case.expected_files,
        latency_ms=lexical_latency,
    )

    vector_hit = hit_at_k(
        vector_results,
        case.expected_files,
        TOP_K,
    )

    lexical_hit = hit_at_k(
        lexical_results,
        case.expected_files,
        TOP_K,
    )

    return (
        vector_hit,
        lexical_hit,
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
            build_diversified_vector_retriever(
                db=db,
                project_id=project_id,
                candidate_k=CANDIDATE_K,
            )
        )

        lexical_retrieve = (
            build_lexical_retriever(
                db=db,
                project_id=project_id,
                candidate_k=CANDIDATE_K,
            )
        )

        vector_hits = 0.0
        lexical_hits = 0.0

        lexical_only_hits: list[str] = []
        vector_only_hits: list[str] = []
        both_hits: list[str] = []
        both_fail: list[str] = []

        for case in cases:
            (
                vector_hit,
                lexical_hit,
            ) = evaluate_case(
                case=case,
                vector_retrieve=vector_retrieve,
                lexical_retrieve=lexical_retrieve,
            )

            vector_hits += vector_hit
            lexical_hits += lexical_hit

            if vector_hit and lexical_hit:
                both_hits.append(
                    case.id
                )

            elif vector_hit and not lexical_hit:
                vector_only_hits.append(
                    case.id
                )

            elif lexical_hit and not vector_hit:
                lexical_only_hits.append(
                    case.id
                )

            else:
                both_fail.append(
                    case.id
                )

        total = len(cases)

        print()
        print()
        print("=" * 80)
        print(
            "VECTOR VS LEXICAL — SUMMARY"
        )
        print("=" * 80)

        print(
            f"Dataset:         "
            f"{dataset_name}"
        )
        print(
            f"Version:         "
            f"{dataset_version}"
        )
        print(
            f"Cases:           "
            f"{total}"
        )

        print()

        print(
            f"Vector Hit@5:    "
            f"{vector_hits / total:.2%}"
        )

        print(
            f"Lexical Hit@5:   "
            f"{lexical_hits / total:.2%}"
        )

        print()
        print(
            "Complementarity"
        )
        print("-" * 80)

        print(
            f"Both hit:        "
            f"{len(both_hits)}"
        )

        print(
            f"Vector only:     "
            f"{len(vector_only_hits)}"
        )

        print(
            f"Lexical only:    "
            f"{len(lexical_only_hits)}"
        )

        print(
            f"Both fail:       "
            f"{len(both_fail)}"
        )

        print()

        print(
            "Lexical-only cases:"
        )

        if lexical_only_hits:
            for case_id in lexical_only_hits:
                print(
                    f"  - {case_id}"
                )
        else:
            print(
                "  - Ninguno"
            )

        print()

        print(
            "Both-fail cases:"
        )

        if both_fail:
            for case_id in both_fail:
                print(
                    f"  - {case_id}"
                )
        else:
            print(
                "  - Ninguno"
            )

    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Compara retrieval vectorial diversificado "
            "con PostgreSQL Full-Text Search."
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

    args = parser.parse_args()

    run(
        project_id=args.project_id,
    )


if __name__ == "__main__":
    main()