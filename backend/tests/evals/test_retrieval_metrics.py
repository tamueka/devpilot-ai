import pytest

from evals.retrieval_metrics import (
    code_ratio_at_k,
    documentation_ratio_at_k,
    hit_at_k,
    mean_metric,
    mean_reciprocal_rank,
    normalize_path,
    recall_at_k,
    reciprocal_rank,
    unique_documents_at_k,
)


def test_normalize_path_converts_windows_separators() -> None:
    result = normalize_path(
        r"backend\app\services\rag_service.py"
    )

    assert result == "backend/app/services/rag_service.py"


def test_normalize_path_removes_relative_prefix() -> None:
    result = normalize_path(
        "./backend/app/services/rag_service.py"
    )

    assert result == "backend/app/services/rag_service.py"


def test_normalize_path_is_case_insensitive() -> None:
    result = normalize_path(
        "Backend/App/Services/RAG_SERVICE.py"
    )

    assert result == "backend/app/services/rag_service.py"


def test_hit_at_1_returns_one_when_first_result_is_relevant() -> None:
    retrieved = [
        "backend/app/services/rag_service.py",
        "backend/app/services/readme_service.py",
    ]

    expected = [
        "backend/app/services/rag_service.py",
    ]

    assert hit_at_k(retrieved, expected, 1) == 1.0


def test_hit_at_1_returns_zero_when_relevant_result_is_second() -> None:
    retrieved = [
        "backend/app/services/readme_service.py",
        "backend/app/services/rag_service.py",
    ]

    expected = [
        "backend/app/services/rag_service.py",
    ]

    assert hit_at_k(retrieved, expected, 1) == 0.0


def test_hit_at_3_returns_one_when_relevant_result_is_second() -> None:
    retrieved = [
        "backend/app/services/readme_service.py",
        "backend/app/services/rag_service.py",
        "backend/app/services/unit_test_service.py",
    ]

    expected = [
        "backend/app/services/rag_service.py",
    ]

    assert hit_at_k(retrieved, expected, 3) == 1.0


def test_hit_at_k_matches_windows_and_unix_paths() -> None:
    retrieved = [
        r"backend\app\services\rag_service.py",
    ]

    expected = [
        "backend/app/services/rag_service.py",
    ]

    assert hit_at_k(retrieved, expected, 1) == 1.0


def test_hit_at_k_uses_any_expected_file_as_relevant() -> None:
    retrieved = [
        "backend/app/services/conversation_service.py",
    ]

    expected = [
        "backend/app/services/rag_service.py",
        "backend/app/services/conversation_service.py",
    ]

    assert hit_at_k(retrieved, expected, 1) == 1.0


def test_hit_at_k_returns_zero_for_empty_expected_files() -> None:
    assert hit_at_k(
        ["backend/app/services/rag_service.py"],
        [],
        5,
    ) == 0.0


def test_hit_at_k_rejects_invalid_k() -> None:
    with pytest.raises(
        ValueError,
        match="k must be greater than zero",
    ):
        hit_at_k([], [], 0)


def test_reciprocal_rank_returns_one_for_first_position() -> None:
    retrieved = [
        "backend/app/services/rag_service.py",
    ]

    expected = [
        "backend/app/services/rag_service.py",
    ]

    assert reciprocal_rank(retrieved, expected) == 1.0


def test_reciprocal_rank_returns_half_for_second_position() -> None:
    retrieved = [
        "backend/app/services/readme_service.py",
        "backend/app/services/rag_service.py",
    ]

    expected = [
        "backend/app/services/rag_service.py",
    ]

    assert reciprocal_rank(retrieved, expected) == 0.5


def test_reciprocal_rank_returns_zero_when_no_result_is_relevant() -> None:
    retrieved = [
        "backend/app/services/readme_service.py",
    ]

    expected = [
        "backend/app/services/rag_service.py",
    ]

    assert reciprocal_rank(retrieved, expected) == 0.0


def test_recall_at_5_returns_one_when_all_expected_files_are_found() -> None:
    retrieved = [
        "backend/app/services/rag_service.py",
        "backend/app/services/conversation_service.py",
        "backend/app/services/readme_service.py",
    ]

    expected = [
        "backend/app/services/rag_service.py",
        "backend/app/services/conversation_service.py",
    ]

    assert recall_at_k(retrieved, expected, 5) == 1.0


def test_recall_at_5_returns_half_when_one_of_two_expected_files_is_found() -> None:
    retrieved = [
        "backend/app/services/rag_service.py",
        "backend/app/services/readme_service.py",
    ]

    expected = [
        "backend/app/services/rag_service.py",
        "backend/app/services/conversation_service.py",
    ]

    assert recall_at_k(retrieved, expected, 5) == 0.5


def test_recall_at_k_rejects_invalid_k() -> None:
    with pytest.raises(
        ValueError,
        match="k must be greater than zero",
    ):
        recall_at_k([], [], -1)


def test_mean_reciprocal_rank_calculates_average() -> None:
    result = mean_reciprocal_rank(
        [
            1.0,
            0.5,
            0.0,
        ]
    )

    assert result == pytest.approx(0.5)


def test_mean_reciprocal_rank_returns_zero_for_empty_collection() -> None:
    assert mean_reciprocal_rank([]) == 0.0


def test_mean_metric_calculates_average() -> None:
    result = mean_metric(
        [
            1.0,
            1.0,
            0.0,
            1.0,
        ]
    )

    assert result == pytest.approx(0.75)


def test_mean_metric_returns_zero_for_empty_collection() -> None:
    assert mean_metric([]) == 0.0


def test_unique_documents_at_5_counts_distinct_paths() -> None:
    retrieved = [
        "docs/architecture.md",
        "docs/architecture.md",
        "backend/app/services/rag_service.py",
        "docs/demo.md",
        "backend/app/services/rag_service.py",
    ]

    assert unique_documents_at_k(
        retrieved,
        5,
    ) == 3


def test_unique_documents_at_k_returns_zero_for_empty_results() -> None:
    assert unique_documents_at_k(
        [],
        5,
    ) == 0


def test_unique_documents_at_k_rejects_invalid_k() -> None:
    with pytest.raises(
        ValueError,
        match="k must be greater than zero",
    ):
        unique_documents_at_k(
            [],
            0,
        )


def test_documentation_ratio_at_5() -> None:
    retrieved = [
        "docs/architecture.md",
        "docs/demo.md",
        "backend/app/services/rag_service.py",
        "frontend/src/app/app.ts",
        "README.md",
    ]

    assert documentation_ratio_at_k(
        retrieved,
        5,
    ) == pytest.approx(0.6)


def test_documentation_ratio_returns_zero_for_empty_results() -> None:
    assert documentation_ratio_at_k(
        [],
        5,
    ) == 0.0


def test_code_ratio_at_5() -> None:
    retrieved = [
        "docs/architecture.md",
        "docs/demo.md",
        "backend/app/services/rag_service.py",
        "frontend/src/app/app.ts",
        "README.md",
    ]

    assert code_ratio_at_k(
        retrieved,
        5,
    ) == pytest.approx(0.4)


def test_code_and_documentation_ratios_are_complementary() -> None:
    retrieved = [
        "docs/architecture.md",
        "backend/app/services/rag_service.py",
        "backend/app/security/auth.py",
    ]

    documentation_ratio = documentation_ratio_at_k(
        retrieved,
        5,
    )

    code_ratio = code_ratio_at_k(
        retrieved,
        5,
    )

    assert (
        documentation_ratio + code_ratio
        == pytest.approx(1.0)
    )