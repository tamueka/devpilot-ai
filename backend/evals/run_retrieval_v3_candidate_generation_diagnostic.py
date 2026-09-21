from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from app.db.database import SessionLocal
from evals.lexical_retrieval import (
    build_lexical_retriever,
)
from evals.path_retrieval import (
    build_path_retriever,
)
from evals.retrieval_metrics import normalize_path


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
    / "independent_validation_suite.json"
)

PROJECTS_PATH = (
    BACKEND_ROOT
    / "evals"
    / "datasets"
    / "independent_validation_projects.local.json"
)


TARGET_CASE_IDS = {
    "commitizen-bump-001",
    "axios-adapter-001",
    "axios-headers-001",
    "pinia-subscriptions-001",
}


BASELINE_K = 20
DEEP_K = 100


@dataclass(frozen=True)
class SourceRanks:
    baseline_rank: int | None
    deep_rank: int | None


@dataclass(frozen=True)
class CaseDiagnostic:
    repository: str
    case_id: str
    question: str
    expected_path: str

    lexical: SourceRanks
    path: SourceRanks

    lexical_count: int
    path_count: int


def load_json(
    path: Path,
) -> dict:
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
        raise ValueError(
            f"Expected JSON object: {path}"
        )

    return payload


def get_case_id(
    case: dict,
) -> str:
    value = case.get(
        "id",
    )

    if value is None:
        value = case.get(
            "case_id",
        )

    if (
        not isinstance(
            value,
            str,
        )
        or not value.strip()
    ):
        raise ValueError(
            "Evaluation case has no valid id"
        )

    return value


def get_question(
    case: dict,
) -> str:
    value = case.get(
        "question",
    )

    if (
        not isinstance(
            value,
            str,
        )
        or not value.strip()
    ):
        raise ValueError(
            "Evaluation case has no valid question"
        )

    return value


def get_expected_path(
    case: dict,
) -> str:
    expected_files = case.get(
        "expected_files",
    )

    if (
        not isinstance(
            expected_files,
            list,
        )
        or not expected_files
    ):
        raise ValueError(
            "Evaluation case has no expected_files"
        )

    first_path = expected_files[
        0
    ]

    if (
        not isinstance(
            first_path,
            str,
        )
        or not first_path.strip()
    ):
        raise ValueError(
            "Invalid expected path"
        )

    return first_path


def find_rank(
    paths: list[str],
    expected_path: str,
) -> int | None:
    normalized_expected = (
        normalize_path(
            expected_path
        )
    )

    for rank, path in enumerate(
        paths,
        start=1,
    ):
        if (
            normalize_path(
                path
            )
            == normalized_expected
        ):
            return rank

    return None


def build_source_ranks(
    *,
    paths: list[str],
    expected_path: str,
) -> SourceRanks:
    baseline_paths = paths[
        :BASELINE_K
    ]

    return SourceRanks(
        baseline_rank=find_rank(
            baseline_paths,
            expected_path,
        ),
        deep_rank=find_rank(
            paths,
            expected_path,
        ),
    )


def format_rank(
    rank: int | None,
) -> str:
    if rank is None:
        return "MISS"

    return str(
        rank
    )


def classify(
    diagnostic: CaseDiagnostic,
) -> str:
    lexical_rank = (
        diagnostic.lexical.deep_rank
    )

    path_rank = (
        diagnostic.path.deep_rank
    )

    if (
        lexical_rank is None
        and path_rank is None
    ):
        return "ABSENT_IN_LEXICAL_AND_PATH_AT_100"

    sources: list[str] = []

    if lexical_rank is not None:
        sources.append(
            "LEXICAL"
        )

    if path_rank is not None:
        sources.append(
            "PATH"
        )

    return "+".join(
        sources
    )


def print_case(
    diagnostic: CaseDiagnostic,
) -> None:
    print()
    print("=" * 110)

    print(
        f"{diagnostic.repository} | "
        f"{diagnostic.case_id}"
    )

    print("=" * 110)

    print(
        f"Question: {diagnostic.question}"
    )

    print(
        f"Expected: {diagnostic.expected_path}"
    )

    print()

    print(
        "Vector deep diagnostic: SKIPPED"
    )

    print(
        "Reason: embedding API quota unavailable."
    )

    print()

    print(
        f"Lexical@20:  "
        f"{format_rank(diagnostic.lexical.baseline_rank)}"
    )

    print(
        f"Lexical@100: "
        f"{format_rank(diagnostic.lexical.deep_rank)}"
        f"  "
        f"(returned {diagnostic.lexical_count})"
    )

    print()

    print(
        f"Path@20:     "
        f"{format_rank(diagnostic.path.baseline_rank)}"
    )

    print(
        f"Path@100:    "
        f"{format_rank(diagnostic.path.deep_rank)}"
        f"  "
        f"(returned {diagnostic.path_count})"
    )

    print()

    print(
        f"Deep coverage: "
        f"{classify(diagnostic)}"
    )


def print_summary(
    diagnostics: list[
        CaseDiagnostic
    ],
) -> None:
    print()
    print()
    print("=" * 110)

    print(
        "DEVPILOT AI - "
        "RETRIEVAL V3 DEEP CANDIDATE DIAGNOSTIC"
    )

    print("=" * 110)

    print()

    print(
        f"Cases: {len(diagnostics)}"
    )

    lexical_hits = sum(
        diagnostic.lexical.deep_rank
        is not None
        for diagnostic in diagnostics
    )

    path_hits = sum(
        diagnostic.path.deep_rank
        is not None
        for diagnostic in diagnostics
    )

    union_hits = sum(
        (
            diagnostic.lexical.deep_rank
            is not None
        )
        or (
            diagnostic.path.deep_rank
            is not None
        )
        for diagnostic in diagnostics
    )

    print()
    print(
        "Deep candidate coverage"
    )

    print("-" * 110)

    print(
        "Vector@100:   SKIPPED"
    )

    print(
        f"Lexical@100:  "
        f"{lexical_hits}/{len(diagnostics)}"
    )

    print(
        f"Path@100:     "
        f"{path_hits}/{len(diagnostics)}"
    )

    print(
        f"Union L+P:    "
        f"{union_hits}/{len(diagnostics)}"
    )

    print()
    print(
        "Per-case classification"
    )

    print("-" * 110)

    for diagnostic in diagnostics:
        print(
            f"{diagnostic.case_id:<30} "
            f"{classify(diagnostic)}"
        )


def main() -> None:
    suite = load_json(
        SUITE_PATH
    )

    project_mapping = load_json(
        PROJECTS_PATH
    )

    repositories = suite.get(
        "repositories",
    )

    projects = project_mapping.get(
        "projects",
    )

    if not isinstance(
        repositories,
        list,
    ):
        raise ValueError(
            "Suite does not contain repositories"
        )

    if not isinstance(
        projects,
        dict,
    ):
        raise ValueError(
            "Project mapping does not contain projects"
        )

    diagnostics: list[
        CaseDiagnostic
    ] = []

    found_cases: set[str] = set()

    print()
    print("=" * 110)

    print(
        "DEVPILOT AI - "
        "RETRIEVAL V3 DEEP CANDIDATE DIAGNOSTIC"
    )

    print("=" * 110)

    print()

    print(
        "Diagnostic only."
    )

    print(
        "No LLM reranking is executed."
    )

    print(
        "Vector deep retrieval skipped: "
        "embedding API quota unavailable."
    )

    print(
        f"Deep document depth: "
        f"{DEEP_K}"
    )

    for repository in repositories:
        if not isinstance(
            repository,
            dict,
        ):
            continue

        repository_key = (
            repository.get(
                "key",
            )
        )

        dataset_relative_path = (
            repository.get(
                "dataset",
            )
        )

        if (
            not isinstance(
                repository_key,
                str,
            )
            or not isinstance(
                dataset_relative_path,
                str,
            )
        ):
            raise ValueError(
                "Invalid repository entry"
            )

        project_entry = projects.get(
            repository_key,
        )

        if not isinstance(
            project_entry,
            dict,
        ):
            raise ValueError(
                f"Missing project mapping: "
                f"{repository_key}"
            )

        project_id_value = (
            project_entry.get(
                "project_id",
            )
        )

        if not isinstance(
            project_id_value,
            str,
        ):
            raise ValueError(
                f"Invalid project id: "
                f"{repository_key}"
            )

        project_id = UUID(
            project_id_value
        )

        dataset_path = (
            BACKEND_ROOT
            / dataset_relative_path
        ).resolve()

        dataset = load_json(
            dataset_path
        )

        cases = dataset.get(
            "cases",
        )

        if not isinstance(
            cases,
            list,
        ):
            raise ValueError(
                f"Dataset has no cases: "
                f"{dataset_path}"
            )

        target_cases = [
            case
            for case in cases
            if (
                isinstance(
                    case,
                    dict,
                )
                and get_case_id(
                    case
                )
                in TARGET_CASE_IDS
            )
        ]

        if not target_cases:
            continue

        print()
        print(
            f"Preparing retrievers for "
            f"{repository_key}..."
        )

        db = SessionLocal()

        try:
            lexical_retrieve = (
                build_lexical_retriever(
                    db=db,
                    project_id=project_id,
                    candidate_k=DEEP_K,
                )
            )

            path_retrieve = (
                build_path_retriever(
                    db=db,
                    project_id=project_id,
                    candidate_k=DEEP_K,
                )
            )

            for case in target_cases:
                case_id = get_case_id(
                    case
                )

                question = get_question(
                    case
                )

                expected_path = (
                    get_expected_path(
                        case
                    )
                )

                print(
                    f"  Processing "
                    f"{case_id}..."
                )

                lexical_files = list(
                    lexical_retrieve(
                        question,
                        DEEP_K,
                    )
                )

                path_files = list(
                    path_retrieve(
                        question,
                        DEEP_K,
                    )
                )

                diagnostic = (
                    CaseDiagnostic(
                        repository=(
                            repository_key
                        ),
                        case_id=case_id,
                        question=question,
                        expected_path=(
                            expected_path
                        ),
                        lexical=build_source_ranks(
                            paths=lexical_files,
                            expected_path=(
                                expected_path
                            ),
                        ),
                        path=build_source_ranks(
                            paths=path_files,
                            expected_path=(
                                expected_path
                            ),
                        ),
                        lexical_count=len(
                            lexical_files
                        ),
                        path_count=len(
                            path_files
                        ),
                    )
                )

                diagnostics.append(
                    diagnostic
                )

                found_cases.add(
                    case_id
                )

        finally:
            db.close()

    missing_cases = (
        TARGET_CASE_IDS
        - found_cases
    )

    if missing_cases:
        raise RuntimeError(
            "Missing target cases: "
            + ", ".join(
                sorted(
                    missing_cases
                )
            )
        )

    if (
        len(diagnostics)
        != len(TARGET_CASE_IDS)
    ):
        raise RuntimeError(
            "Unexpected diagnostic count: "
            f"{len(diagnostics)}"
        )

    for diagnostic in diagnostics:
        print_case(
            diagnostic
        )

    print_summary(
        diagnostics
    )


if __name__ == "__main__":
    main()