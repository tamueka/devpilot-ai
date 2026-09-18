from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from evals.evaluator import (
    CaseEvaluationResult,
    EvaluationCase,
    build_summary,
    evaluate_case,
    evaluate_dataset,
    load_dataset,
)


def create_case() -> EvaluationCase:
    return EvaluationCase(
        id="test-001",
        category="test",
        question=(
            "¿Dónde está implementado "
            "el servicio?"
        ),
        expected_files=(
            "backend/app/service.py",
        ),
    )


def create_result(
    *,
    case_id: str = "test-001",
    hit_at_1: float = 1.0,
    hit_at_3: float = 1.0,
    hit_at_5: float = 1.0,
    recall_at_5: float = 1.0,
    reciprocal_rank_value: float = 1.0,
    unique_documents_at_5: int = 5,
    documentation_ratio_at_5: float = 0.2,
    code_ratio_at_5: float = 0.8,
    latency_ms: float = 100.0,
) -> CaseEvaluationResult:
    return CaseEvaluationResult(
        case_id=case_id,
        category="test",
        question="Pregunta",
        expected_files=(
            "backend/app/service.py",
        ),
        retrieved_files=(
            "backend/app/service.py",
            "backend/app/other.py",
            "docs/readme.md",
            "backend/app/a.py",
            "backend/app/b.py",
        ),
        hit_at_1=hit_at_1,
        hit_at_3=hit_at_3,
        hit_at_5=hit_at_5,
        recall_at_5=recall_at_5,
        reciprocal_rank=(
            reciprocal_rank_value
        ),
        unique_documents_at_5=(
            unique_documents_at_5
        ),
        documentation_ratio_at_5=(
            documentation_ratio_at_5
        ),
        code_ratio_at_5=(
            code_ratio_at_5
        ),
        latency_ms=latency_ms,
    )


def write_dataset(
    path: Path,
    *,
    name: str = "Test Dataset",
    version: str = "1.0",
) -> None:
    path.write_text(
        json.dumps(
            {
                "metadata": {
                    "name": name,
                    "version": version,
                    "description": (
                        "Dataset utilizado por tests."
                    ),
                },
                "cases": [
                    {
                        "id": "custom-001",
                        "category": "test",
                        "question": (
                            "¿Dónde está el servicio?"
                        ),
                        "expected_files": [
                            "backend/app/service.py"
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_load_dataset_supports_custom_path(
    tmp_path: Path,
) -> None:
    dataset_path = (
        tmp_path
        / "custom_eval.json"
    )

    write_dataset(
        dataset_path,
        name="Custom Dataset",
        version="test-1",
    )

    name, version, cases = load_dataset(
        dataset_path
    )

    assert name == "Custom Dataset"
    assert version == "test-1"

    assert len(cases) == 1

    assert cases[0].id == (
        "custom-001"
    )

    assert cases[0].category == (
        "test"
    )

    assert cases[0].question == (
        "¿Dónde está el servicio?"
    )

    assert cases[0].expected_files == (
        "backend/app/service.py",
    )


def test_load_dataset_accepts_path_as_string(
    tmp_path: Path,
) -> None:
    dataset_path = (
        tmp_path
        / "custom_eval.json"
    )

    write_dataset(
        dataset_path
    )

    name, version, cases = load_dataset(
        str(
            dataset_path
        )
    )

    assert name == "Test Dataset"
    assert version == "1.0"
    assert len(cases) == 1


def test_load_dataset_rejects_missing_path(
    tmp_path: Path,
) -> None:
    missing_path = (
        tmp_path
        / "missing.json"
    )

    with pytest.raises(
        FileNotFoundError,
        match="Evaluation dataset not found",
    ):
        load_dataset(
            missing_path
        )


def test_load_dataset_rejects_missing_metadata(
    tmp_path: Path,
) -> None:
    dataset_path = (
        tmp_path
        / "invalid.json"
    )

    dataset_path.write_text(
        json.dumps(
            {
                "cases": [],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match=(
            "Evaluation dataset "
            "must contain metadata"
        ),
    ):
        load_dataset(
            dataset_path
        )


def test_load_dataset_rejects_invalid_cases(
    tmp_path: Path,
) -> None:
    dataset_path = (
        tmp_path
        / "invalid.json"
    )

    dataset_path.write_text(
        json.dumps(
            {
                "metadata": {
                    "name": "Test",
                    "version": "1.0",
                },
                "cases": "not-a-list",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match=(
            "Evaluation dataset cases "
            "must be a list"
        ),
    ):
        load_dataset(
            dataset_path
        )


def test_load_dataset_requires_expected_files(
    tmp_path: Path,
) -> None:
    dataset_path = (
        tmp_path
        / "invalid.json"
    )

    dataset_path.write_text(
        json.dumps(
            {
                "metadata": {
                    "name": "Test",
                    "version": "1.0",
                },
                "cases": [
                    {
                        "id": "case-001",
                        "category": "test",
                        "question": "Pregunta",
                        "expected_files": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match=(
            "must contain at least "
            "one expected file"
        ),
    ):
        load_dataset(
            dataset_path
        )


def test_evaluate_case_calculates_metrics() -> None:
    case = create_case()

    retrieve = MagicMock(
        return_value=[
            "backend/app/other.py",
            "backend/app/service.py",
            "docs/readme.md",
            "backend/app/a.py",
            "backend/app/b.py",
        ]
    )

    with patch(
        "evals.evaluator.perf_counter",
        side_effect=[
            10.0,
            10.025,
        ],
    ):
        result = evaluate_case(
            case=case,
            retrieve=retrieve,
            retrieval_k=5,
        )

    retrieve.assert_called_once_with(
        case.question,
        5,
    )

    assert result.case_id == (
        "test-001"
    )

    assert result.category == (
        "test"
    )

    assert result.question == (
        case.question
    )

    assert result.expected_files == (
        "backend/app/service.py",
    )

    assert result.retrieved_files == (
        "backend/app/other.py",
        "backend/app/service.py",
        "docs/readme.md",
        "backend/app/a.py",
        "backend/app/b.py",
    )

    assert result.hit_at_1 == 0.0
    assert result.hit_at_3 == 1.0
    assert result.hit_at_5 == 1.0
    assert result.recall_at_5 == 1.0
    assert result.reciprocal_rank == 0.5

    assert (
        result.unique_documents_at_5
        == 5
    )

    assert (
        result.documentation_ratio_at_5
        == pytest.approx(
            0.2
        )
    )

    assert (
        result.code_ratio_at_5
        == pytest.approx(
            0.8
        )
    )

    assert result.latency_ms == (
        pytest.approx(
            25.0
        )
    )


def test_evaluate_case_rejects_retrieval_k_below_five() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "retrieval_k must be greater "
            "than or equal to 5"
        ),
    ):
        evaluate_case(
            case=create_case(),
            retrieve=MagicMock(),
            retrieval_k=4,
        )


def test_build_summary_calculates_averages() -> None:
    results = [
        create_result(
            case_id="case-001",
            hit_at_1=1.0,
            hit_at_3=1.0,
            hit_at_5=1.0,
            recall_at_5=1.0,
            reciprocal_rank_value=1.0,
            unique_documents_at_5=5,
            documentation_ratio_at_5=0.2,
            code_ratio_at_5=0.8,
            latency_ms=100.0,
        ),
        create_result(
            case_id="case-002",
            hit_at_1=0.0,
            hit_at_3=1.0,
            hit_at_5=1.0,
            recall_at_5=0.5,
            reciprocal_rank_value=0.5,
            unique_documents_at_5=3,
            documentation_ratio_at_5=0.6,
            code_ratio_at_5=0.4,
            latency_ms=300.0,
        ),
    ]

    summary = build_summary(
        results
    )

    assert summary.total_cases == 2

    assert summary.hit_at_1 == (
        pytest.approx(
            0.5
        )
    )

    assert summary.hit_at_3 == (
        pytest.approx(
            1.0
        )
    )

    assert summary.hit_at_5 == (
        pytest.approx(
            1.0
        )
    )

    assert summary.recall_at_5 == (
        pytest.approx(
            0.75
        )
    )

    assert summary.mrr == (
        pytest.approx(
            0.75
        )
    )

    assert (
        summary.average_unique_documents_at_5
        == pytest.approx(
            4.0
        )
    )

    assert (
        summary.average_documentation_ratio_at_5
        == pytest.approx(
            0.4
        )
    )

    assert (
        summary.average_code_ratio_at_5
        == pytest.approx(
            0.6
        )
    )

    assert (
        summary.average_latency_ms
        == pytest.approx(
            200.0
        )
    )


def test_build_summary_handles_empty_results() -> None:
    summary = build_summary(
        []
    )

    assert summary.total_cases == 0
    assert summary.hit_at_1 == 0.0
    assert summary.hit_at_3 == 0.0
    assert summary.hit_at_5 == 0.0
    assert summary.recall_at_5 == 0.0
    assert summary.mrr == 0.0

    assert (
        summary.average_unique_documents_at_5
        == 0.0
    )

    assert (
        summary.average_documentation_ratio_at_5
        == 0.0
    )

    assert (
        summary.average_code_ratio_at_5
        == 0.0
    )

    assert (
        summary.average_latency_ms
        == 0.0
    )


def test_evaluate_dataset_supports_custom_dataset(
    tmp_path: Path,
) -> None:
    dataset_path = (
        tmp_path
        / "custom_eval.json"
    )

    write_dataset(
        dataset_path,
        name="Held-out Dataset",
        version="2.0",
    )

    retrieve = MagicMock(
        return_value=[
            "backend/app/service.py",
            "backend/app/other.py",
            "docs/readme.md",
            "backend/app/a.py",
            "backend/app/b.py",
        ]
    )

    report = evaluate_dataset(
        retrieve=retrieve,
        retrieval_k=5,
        dataset_path=dataset_path,
    )

    assert report.dataset_name == (
        "Held-out Dataset"
    )

    assert report.dataset_version == (
        "2.0"
    )

    assert len(
        report.results
    ) == 1

    assert (
        report.results[0].case_id
        == "custom-001"
    )

    assert (
        report.summary.total_cases
        == 1
    )

    assert (
        report.summary.hit_at_1
        == 1.0
    )

    retrieve.assert_called_once_with(
        "¿Dónde está el servicio?",
        5,
    )


def test_evaluate_dataset_rejects_retrieval_k_below_five(
    tmp_path: Path,
) -> None:
    dataset_path = (
        tmp_path
        / "custom_eval.json"
    )

    write_dataset(
        dataset_path
    )

    retrieve = MagicMock()

    with pytest.raises(
        ValueError,
        match=(
            "retrieval_k must be greater "
            "than or equal to 5"
        ),
    ):
        evaluate_dataset(
            retrieve=retrieve,
            retrieval_k=4,
            dataset_path=dataset_path,
        )

    retrieve.assert_not_called()