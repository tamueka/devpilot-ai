from __future__ import annotations

import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from app.db.database import SessionLocal
from evals.multi_source_candidate_retrieval import (
    DEFAULT_LEXICAL_DOCUMENT_K,
    DEFAULT_PATH_DOCUMENT_K,
    DEFAULT_VECTOR_DOCUMENT_K,
    MultiSourceCandidates,
    build_multi_source_candidate_collector,
)
from evals.multi_source_fusion import (
    MultiSourceFusionResult,
    best_rank_fusion,
)
from evals.retrieval_metrics import normalize_path
from evals.retrieval_v2 import (
    DEFAULT_RETRIEVAL_V2_CANDIDATE_K,
)


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


FAILURE_CASE_IDS = {
    "commitizen-bump-001",
    "commitizen-config-001",
    "commitizen-plugins-001",
    "axios-adapter-001",
    "axios-headers-001",
    "axios-merge-config-001",
    "axios-proxy-001",
    "pinia-define-store-001",
    "pinia-subscriptions-001",
    "pinia-devtools-plugin-001",
}


CANDIDATE_GENERATION_FAILURE = (
    "CANDIDATE_GENERATION"
)

FUSION_CUTOFF_FAILURE = (
    "FUSION_CUTOFF"
)

RERANKER_FAILURE = (
    "RERANKER"
)


@dataclass(frozen=True)
class ExpectedFileDiagnostic:
    path: str

    vector_rank: int | None
    lexical_rank: int | None
    path_rank: int | None

    fusion_rank: int | None

    in_union: bool
    in_top_10: bool


@dataclass(frozen=True)
class CaseDiagnostic:
    repository: str
    case_id: str
    category: str
    expected_files: tuple[str, ...]

    expected_diagnostics: tuple[
        ExpectedFileDiagnostic,
        ...
    ]

    vector_candidate_count: int
    lexical_candidate_count: int
    path_candidate_count: int
    union_candidate_count: int

    classification: str


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
            "Evaluation case does not contain "
            "a valid id/case_id"
        )

    return value


def get_case_category(
    case: dict,
) -> str:
    value = case.get(
        "category",
        "",
    )

    if not isinstance(
        value,
        str,
    ):
        return ""

    return value


def get_case_question(
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
            "Evaluation case does not contain "
            "a valid question"
        )

    return value


def get_expected_files(
    case: dict,
) -> tuple[str, ...]:
    value = case.get(
        "expected_files",
    )

    if not isinstance(
        value,
        list,
    ):
        raise ValueError(
            "Evaluation case does not contain "
            "expected_files"
        )

    files = tuple(
        path
        for path in value
        if isinstance(
            path,
            str,
        )
        and path.strip()
    )

    if not files:
        raise ValueError(
            "Evaluation case contains no "
            "valid expected files"
        )

    return files


def find_rank(
    paths: tuple[str, ...],
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


def find_fusion_rank(
    fusion_results: list[
        MultiSourceFusionResult
    ],
    expected_path: str,
) -> int | None:
    normalized_expected = (
        normalize_path(
            expected_path
        )
    )

    for rank, result in enumerate(
        fusion_results,
        start=1,
    ):
        if (
            normalize_path(
                result.path
            )
            == normalized_expected
        ):
            return rank

    return None


def diagnose_expected_file(
    *,
    candidates: MultiSourceCandidates,
    fusion_results: list[
        MultiSourceFusionResult
    ],
    expected_path: str,
) -> ExpectedFileDiagnostic:
    vector_rank = find_rank(
        candidates.vector_files,
        expected_path,
    )

    lexical_rank = find_rank(
        candidates.lexical_files,
        expected_path,
    )

    path_rank = find_rank(
        candidates.path_files,
        expected_path,
    )

    fusion_rank = find_fusion_rank(
        fusion_results,
        expected_path,
    )

    in_union = any(
        rank is not None
        for rank in (
            vector_rank,
            lexical_rank,
            path_rank,
        )
    )

    in_top_10 = (
        fusion_rank is not None
        and fusion_rank
        <= DEFAULT_RETRIEVAL_V2_CANDIDATE_K
    )

    return ExpectedFileDiagnostic(
        path=expected_path,
        vector_rank=vector_rank,
        lexical_rank=lexical_rank,
        path_rank=path_rank,
        fusion_rank=fusion_rank,
        in_union=in_union,
        in_top_10=in_top_10,
    )


def classify_case(
    diagnostics: tuple[
        ExpectedFileDiagnostic,
        ...
    ],
) -> str:
    if any(
        diagnostic.in_top_10
        for diagnostic in diagnostics
    ):
        return RERANKER_FAILURE

    if any(
        diagnostic.in_union
        for diagnostic in diagnostics
    ):
        return FUSION_CUTOFF_FAILURE

    return CANDIDATE_GENERATION_FAILURE


def format_rank(
    rank: int | None,
) -> str:
    if rank is None:
        return "MISS"

    return str(
        rank
    )


def print_case_diagnostic(
    diagnostic: CaseDiagnostic,
) -> None:
    print()
    print("=" * 110)

    print(
        f"{diagnostic.repository} | "
        f"{diagnostic.case_id} | "
        f"{diagnostic.category}"
    )

    print("=" * 110)

    print(
        f"Classification: "
        f"{diagnostic.classification}"
    )

    print()

    print(
        "Candidate counts:"
    )

    print(
        f"  Vector:  "
        f"{diagnostic.vector_candidate_count}"
    )

    print(
        f"  Lexical: "
        f"{diagnostic.lexical_candidate_count}"
    )

    print(
        f"  Path:    "
        f"{diagnostic.path_candidate_count}"
    )

    print(
        f"  Union:   "
        f"{diagnostic.union_candidate_count}"
    )

    print()

    for expected in (
        diagnostic.expected_diagnostics
    ):
        print(
            f"Expected: {expected.path}"
        )

        print(
            f"  Vector@20:       "
            f"{format_rank(expected.vector_rank)}"
        )

        print(
            f"  Lexical@20:      "
            f"{format_rank(expected.lexical_rank)}"
        )

        print(
            f"  Path@20:         "
            f"{format_rank(expected.path_rank)}"
        )

        print(
            f"  Best-Rank global:"
            f" {format_rank(expected.fusion_rank)}"
        )

        print(
            f"  Best-Rank Top10: "
            f"{'YES' if expected.in_top_10 else 'NO'}"
        )


def print_summary(
    diagnostics: list[
        CaseDiagnostic
    ],
) -> None:
    classification_counts = Counter(
        diagnostic.classification
        for diagnostic in diagnostics
    )

    total = len(
        diagnostics
    )

    vector_hits = sum(
        1
        for diagnostic in diagnostics
        if any(
            expected.vector_rank
            is not None
            for expected
            in diagnostic.expected_diagnostics
        )
    )

    lexical_hits = sum(
        1
        for diagnostic in diagnostics
        if any(
            expected.lexical_rank
            is not None
            for expected
            in diagnostic.expected_diagnostics
        )
    )

    path_hits = sum(
        1
        for diagnostic in diagnostics
        if any(
            expected.path_rank
            is not None
            for expected
            in diagnostic.expected_diagnostics
        )
    )

    union_hits = sum(
        1
        for diagnostic in diagnostics
        if any(
            expected.in_union
            for expected
            in diagnostic.expected_diagnostics
        )
    )

    top_10_hits = sum(
        1
        for diagnostic in diagnostics
        if any(
            expected.in_top_10
            for expected
            in diagnostic.expected_diagnostics
        )
    )

    print()
    print()
    print("=" * 110)

    print(
        "DEVPILOT AI - "
        "RETRIEVAL V3 FAILURE DIAGNOSTIC"
    )

    print("=" * 110)

    print(
        f"Failed Retrieval v2 cases: "
        f"{total}"
    )

    print()
    print(
        "Candidate coverage"
    )

    print("-" * 110)

    print(
        f"Vector@20:        "
        f"{vector_hits}/{total}"
    )

    print(
        f"Lexical@20:       "
        f"{lexical_hits}/{total}"
    )

    print(
        f"Path@20:          "
        f"{path_hits}/{total}"
    )

    print(
        f"Union V+L+P:      "
        f"{union_hits}/{total}"
    )

    print(
        f"Best-Rank Top10:  "
        f"{top_10_hits}/{total}"
    )

    print()
    print(
        "Failure classification"
    )

    print("-" * 110)

    print(
        f"Candidate generation: "
        f"{classification_counts[CANDIDATE_GENERATION_FAILURE]}"
    )

    print(
        f"Fusion / cutoff:      "
        f"{classification_counts[FUSION_CUTOFF_FAILURE]}"
    )

    print(
        f"Reranker:             "
        f"{classification_counts[RERANKER_FAILURE]}"
    )

    print()
    print(
        "Interpretation"
    )

    print("-" * 110)

    print(
        "CANDIDATE_GENERATION = expected file is absent "
        "from Vector@20, Lexical@20 and Path@20."
    )

    print(
        "FUSION_CUTOFF = expected file exists in the "
        "multi-source union but falls below Best-Rank Top10."
    )

    print(
        "RERANKER = expected file reaches Best-Rank Top10 "
        "but was absent from the final Retrieval v2 Top5."
    )


def main() -> None:
    suite = load_json(
        SUITE_PATH
    )

    projects_payload = load_json(
        PROJECTS_PATH
    )

    repositories = suite.get(
        "repositories",
    )

    if not isinstance(
        repositories,
        list,
    ):
        raise ValueError(
            "Validation suite does not contain repositories"
        )

    projects = projects_payload.get(
        "projects",
    )

    if not isinstance(
        projects,
        dict,
    ):
        raise ValueError(
            "Local project mapping does not contain projects"
        )

    diagnostics: list[
        CaseDiagnostic
    ] = []

    found_failure_ids: set[str] = set()

    print()
    print("=" * 110)

    print(
        "DEVPILOT AI - "
        "RETRIEVAL V3 FAILURE DIAGNOSTIC"
    )

    print("=" * 110)

    print()
    print(
        "Analyzing the 10 failed cases from "
        "Retrieval v2 independent validation."
    )

    print(
        "Retrieval v2 remains unchanged."
    )

    for repository in repositories:
        if not isinstance(
            repository,
            dict,
        ):
            continue

        repository_key = repository.get(
            "key",
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
                "Invalid repository entry "
                "in validation suite"
            )

        project_entry = projects.get(
            repository_key,
        )

        if not isinstance(
            project_entry,
            dict,
        ):
            raise ValueError(
                f"Missing local project mapping: "
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
                f"Invalid project_id for "
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
                f"Dataset does not contain cases: "
                f"{dataset_path}"
            )

        repository_failure_cases = []

        for case in cases:
            if not isinstance(
                case,
                dict,
            ):
                continue

            case_id = get_case_id(
                case
            )

            if (
                case_id
                not in FAILURE_CASE_IDS
            ):
                continue

            repository_failure_cases.append(
                case
            )

        if not repository_failure_cases:
            continue

        print()
        print(
            f"Building candidate collector for "
            f"{repository_key}..."
        )

        db = SessionLocal()

        try:
            collect_candidates = (
                build_multi_source_candidate_collector(
                    db=db,
                    project_id=project_id,
                    vector_document_k=(
                        DEFAULT_VECTOR_DOCUMENT_K
                    ),
                    lexical_document_k=(
                        DEFAULT_LEXICAL_DOCUMENT_K
                    ),
                    path_document_k=(
                        DEFAULT_PATH_DOCUMENT_K
                    ),
                )
            )

            for case in (
                repository_failure_cases
            ):
                case_id = get_case_id(
                    case
                )

                category = get_case_category(
                    case
                )

                question = get_case_question(
                    case
                )

                expected_files = (
                    get_expected_files(
                        case
                    )
                )

                print(
                    f"  Processing {case_id}..."
                )

                candidates = (
                    collect_candidates(
                        question
                    )
                )

                fusion_results = (
                    best_rank_fusion(
                        candidates,
                        final_k=max(
                            1,
                            len(
                                candidates.union_files
                            ),
                        ),
                    )
                )

                expected_diagnostics = tuple(
                    diagnose_expected_file(
                        candidates=candidates,
                        fusion_results=(
                            fusion_results
                        ),
                        expected_path=(
                            expected_path
                        ),
                    )
                    for expected_path
                    in expected_files
                )

                classification = (
                    classify_case(
                        expected_diagnostics
                    )
                )

                diagnostic = (
                    CaseDiagnostic(
                        repository=(
                            repository_key
                        ),
                        case_id=case_id,
                        category=category,
                        expected_files=(
                            expected_files
                        ),
                        expected_diagnostics=(
                            expected_diagnostics
                        ),
                        vector_candidate_count=len(
                            candidates.vector_files
                        ),
                        lexical_candidate_count=len(
                            candidates.lexical_files
                        ),
                        path_candidate_count=len(
                            candidates.path_files
                        ),
                        union_candidate_count=len(
                            candidates.union_files
                        ),
                        classification=(
                            classification
                        ),
                    )
                )

                diagnostics.append(
                    diagnostic
                )

                found_failure_ids.add(
                    case_id
                )

        finally:
            db.close()

    missing_failure_ids = (
        FAILURE_CASE_IDS
        - found_failure_ids
    )

    if missing_failure_ids:
        raise RuntimeError(
            "Some expected failure cases were not found: "
            + ", ".join(
                sorted(
                    missing_failure_ids
                )
            )
        )

    if len(
        diagnostics
    ) != len(
        FAILURE_CASE_IDS
    ):
        raise RuntimeError(
            "Unexpected number of diagnostics: "
            f"{len(diagnostics)}"
        )

    for diagnostic in diagnostics:
        print_case_diagnostic(
            diagnostic
        )

    print_summary(
        diagnostics
    )


if __name__ == "__main__":
    main()