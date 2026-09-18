from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from uuid import UUID

from app.db.database import SessionLocal
from evals.diversified_vector_retrieval import (
    build_diversified_vector_retriever,
)
from evals.evaluator import load_dataset
from evals.hybrid_retrieval import (
    reciprocal_rank_fusion,
)
from evals.lexical_retrieval import (
    build_lexical_retriever,
)
from evals.retrieval_metrics import (
    hit_at_k,
    mean_metric,
    mean_reciprocal_rank,
    recall_at_k,
    reciprocal_rank,
)


VECTOR_CANDIDATE_K = 20
LEXICAL_CANDIDATE_K = 20
FINAL_K = 5
RRF_K = 60


@dataclass(frozen=True)
class WeightConfiguration:
    name: str
    vector_weight: float
    lexical_weight: float


@dataclass
class ExperimentMetrics:
    hit_at_1: list[float] = field(
        default_factory=list
    )
    hit_at_3: list[float] = field(
        default_factory=list
    )
    hit_at_5: list[float] = field(
        default_factory=list
    )
    recall_at_5: list[float] = field(
        default_factory=list
    )
    reciprocal_ranks: list[float] = field(
        default_factory=list
    )
    failed_cases: list[str] = field(
        default_factory=list
    )


CONFIGURATIONS = (
    WeightConfiguration(
        name="1.00 : 1.00",
        vector_weight=1.00,
        lexical_weight=1.00,
    ),
    WeightConfiguration(
        name="1.25 : 1.00",
        vector_weight=1.25,
        lexical_weight=1.00,
    ),
    WeightConfiguration(
        name="1.50 : 1.00",
        vector_weight=1.50,
        lexical_weight=1.00,
    ),
    WeightConfiguration(
        name="1.00 : 1.25",
        vector_weight=1.00,
        lexical_weight=1.25,
    ),
    WeightConfiguration(
        name="1.00 : 1.50",
        vector_weight=1.00,
        lexical_weight=1.50,
    ),
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

        metrics = {
            configuration.name: ExperimentMetrics()
            for configuration in CONFIGURATIONS
        }

        print()
        print("=" * 88)
        print(
            "DEVPILOT AI - WEIGHTED RRF EXPERIMENT"
        )
        print("=" * 88)

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
            "Recuperando rankings base "
            "una sola vez por pregunta..."
        )

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
                    VECTOR_CANDIDATE_K,
                )
            )

            lexical_files = list(
                lexical_retrieve(
                    case.question,
                    LEXICAL_CANDIDATE_K,
                )
            )

            for configuration in CONFIGURATIONS:
                fused = reciprocal_rank_fusion(
                    vector_files=vector_files,
                    lexical_files=lexical_files,
                    final_k=FINAL_K,
                    rrf_k=RRF_K,
                    vector_weight=(
                        configuration.vector_weight
                    ),
                    lexical_weight=(
                        configuration.lexical_weight
                    ),
                )

                retrieved_files = [
                    result.path
                    for result in fused
                ]

                current = metrics[
                    configuration.name
                ]

                current.hit_at_1.append(
                    hit_at_k(
                        retrieved_files,
                        case.expected_files,
                        1,
                    )
                )

                current.hit_at_3.append(
                    hit_at_k(
                        retrieved_files,
                        case.expected_files,
                        3,
                    )
                )

                hit_5 = hit_at_k(
                    retrieved_files,
                    case.expected_files,
                    5,
                )

                current.hit_at_5.append(
                    hit_5
                )

                current.recall_at_5.append(
                    recall_at_k(
                        retrieved_files,
                        case.expected_files,
                        5,
                    )
                )

                current.reciprocal_ranks.append(
                    reciprocal_rank(
                        retrieved_files,
                        case.expected_files,
                    )
                )

                if hit_5 == 0.0:
                    current.failed_cases.append(
                        case.id
                    )

        print()
        print()
        print("=" * 88)
        print(
            "WEIGHT COMPARISON"
        )
        print("=" * 88)

        header = (
            f"{'Vector:Lexical':<18}"
            f"{'Hit@1':>10}"
            f"{'Hit@3':>10}"
            f"{'Hit@5':>10}"
            f"{'Recall@5':>12}"
            f"{'MRR':>10}"
        )

        print(
            header
        )
        print(
            "-" * 88
        )

        for configuration in CONFIGURATIONS:
            result = metrics[
                configuration.name
            ]

            hit_1 = mean_metric(
                result.hit_at_1
            )

            hit_3 = mean_metric(
                result.hit_at_3
            )

            hit_5 = mean_metric(
                result.hit_at_5
            )

            recall_5 = mean_metric(
                result.recall_at_5
            )

            mrr = mean_reciprocal_rank(
                result.reciprocal_ranks
            )

            print(
                f"{configuration.name:<18}"
                f"{hit_1:>9.2%}"
                f"{hit_3:>10.2%}"
                f"{hit_5:>10.2%}"
                f"{recall_5:>12.2%}"
                f"{mrr:>10.3f}"
            )

        print()
        print("=" * 88)
        print(
            "FAILED CASES BY CONFIGURATION"
        )
        print("=" * 88)

        for configuration in CONFIGURATIONS:
            result = metrics[
                configuration.name
            ]

            failures = (
                ", ".join(
                    result.failed_cases
                )
                if result.failed_cases
                else "Ninguno"
            )

            print(
                f"{configuration.name:<18}"
                f"{failures}"
            )

        print()
        print(
            "Nota: los rankings Vector y Lexical "
            "se calculan una sola vez por pregunta. "
            "Las cinco configuraciones reutilizan "
            "exactamente los mismos candidatos."
        )

    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Compara diferentes pesos de "
            "Weighted Reciprocal Rank Fusion."
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