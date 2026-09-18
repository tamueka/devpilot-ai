from __future__ import annotations

from unittest.mock import Mock
from uuid import uuid4

import pytest

import evals.retrieval_v2 as module
from evals.multi_source_candidate_retrieval import (
    MultiSourceCandidates,
)
from evals.multi_source_fusion import (
    MultiSourceFusionResult,
)
from evals.retrieval_v2 import (
    build_retrieval_v2_retriever,
)


def build_candidates() -> MultiSourceCandidates:
    return MultiSourceCandidates(
        vector_files=(
            "vector.py",
        ),
        lexical_files=(
            "lexical.py",
        ),
        path_files=(
            "path.py",
        ),
        union_files=(
            "vector.py",
            "lexical.py",
            "path.py",
        ),
    )


def build_fusion_result(
    path: str,
    rank: int,
) -> MultiSourceFusionResult:
    return MultiSourceFusionResult(
        path=path,
        best_rank=rank,
        source_count=1,
        rank_sum=rank,
        vector_rank=rank,
        lexical_rank=None,
        path_rank=None,
    )


def test_retrieval_v2_runs_complete_pipeline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    collector = Mock(
        return_value=build_candidates()
    )

    collector_builder = Mock(
        return_value=collector
    )

    fusion_results = [
        build_fusion_result(
            "candidate-1.py",
            1,
        ),
        build_fusion_result(
            "candidate-2.py",
            2,
        ),
    ]

    fusion = Mock(
        return_value=fusion_results
    )

    reranker = Mock(
        return_value=[
            "candidate-2.py",
            "candidate-1.py",
        ]
    )

    monkeypatch.setattr(
        module,
        "build_multi_source_candidate_collector",
        collector_builder,
    )

    monkeypatch.setattr(
        module,
        "best_rank_fusion",
        fusion,
    )

    monkeypatch.setattr(
        module,
        "rerank_candidate_paths",
        reranker,
    )

    db = Mock()
    project_id = uuid4()
    client = Mock()

    retrieve = build_retrieval_v2_retriever(
        db=db,
        project_id=project_id,
        candidate_k=10,
        model="test-model",
        max_chars_per_document=2000,
        client=client,
    )

    result = retrieve(
        "Where is authentication implemented?",
        5,
    )

    assert result == [
        "candidate-2.py",
        "candidate-1.py",
    ]

    collector_builder.assert_called_once_with(
        db=db,
        project_id=project_id,
    )

    collector.assert_called_once_with(
        "Where is authentication implemented?"
    )

    fusion.assert_called_once_with(
        build_candidates(),
        final_k=10,
    )

    reranker.assert_called_once_with(
        db=db,
        project_id=project_id,
        question=(
            "Where is authentication implemented?"
        ),
        candidate_paths=[
            "candidate-1.py",
            "candidate-2.py",
        ],
        top_k=5,
        client=client,
        model="test-model",
        max_chars_per_document=2000,
    )


def test_retrieval_v2_returns_empty_when_fusion_is_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    collector = Mock(
        return_value=build_candidates()
    )

    monkeypatch.setattr(
        module,
        "build_multi_source_candidate_collector",
        Mock(
            return_value=collector
        ),
    )

    monkeypatch.setattr(
        module,
        "best_rank_fusion",
        Mock(
            return_value=[]
        ),
    )

    reranker = Mock()

    monkeypatch.setattr(
        module,
        "rerank_candidate_paths",
        reranker,
    )

    retrieve = build_retrieval_v2_retriever(
        db=Mock(),
        project_id=uuid4(),
        model="test-model",
    )

    result = retrieve(
        "test question",
        5,
    )

    assert result == []

    reranker.assert_not_called()


@pytest.mark.parametrize(
    (
        "parameter",
        "value",
        "message",
    ),
    [
        (
            "candidate_k",
            0,
            "candidate_k must be greater than zero",
        ),
        (
            "max_chars_per_document",
            0,
            (
                "max_chars_per_document "
                "must be greater than zero"
            ),
        ),
        (
            "model",
            "   ",
            "model must not be blank",
        ),
    ],
)
def test_retrieval_v2_rejects_invalid_configuration(
    parameter: str,
    value,
    message: str,
) -> None:
    kwargs = {
        "candidate_k": 10,
        "max_chars_per_document": 4000,
        "model": "test-model",
    }

    kwargs[
        parameter
    ] = value

    with pytest.raises(
        ValueError,
        match=message,
    ):
        build_retrieval_v2_retriever(
            db=Mock(),
            project_id=uuid4(),
            **kwargs,
        )


def test_retrieval_v2_rejects_blank_question(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        module,
        "build_multi_source_candidate_collector",
        Mock(
            return_value=Mock()
        ),
    )

    retrieve = build_retrieval_v2_retriever(
        db=Mock(),
        project_id=uuid4(),
        model="test-model",
    )

    with pytest.raises(
        ValueError,
        match="question must not be blank",
    ):
        retrieve(
            "   ",
            5,
        )


def test_retrieval_v2_rejects_invalid_final_k(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        module,
        "build_multi_source_candidate_collector",
        Mock(
            return_value=Mock()
        ),
    )

    retrieve = build_retrieval_v2_retriever(
        db=Mock(),
        project_id=uuid4(),
        model="test-model",
    )

    with pytest.raises(
        ValueError,
        match="k must be greater than zero",
    ):
        retrieve(
            "test question",
            0,
        )