from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

from evals.llm_reranker import (
    DEFAULT_MAX_CHARS_PER_DOCUMENT,
    DEFAULT_RERANK_MODEL,
)
from evals.retrieval_v3 import (
    DEFAULT_RETRIEVAL_V3_CANDIDATE_K,
    build_retrieval_v3_retriever,
)


def test_retrieval_v3_uses_twenty_candidates_by_default() -> None:
    assert (
        DEFAULT_RETRIEVAL_V3_CANDIDATE_K
        == 20
    )


@patch(
    "evals.retrieval_v3."
    "build_retrieval_v2_retriever"
)
def test_retrieval_v3_delegates_to_stable_pipeline(
    build_v2_mock: MagicMock,
) -> None:
    db = MagicMock()
    project_id = uuid4()
    client = MagicMock()

    expected_retriever = MagicMock()

    build_v2_mock.return_value = (
        expected_retriever
    )

    result = build_retrieval_v3_retriever(
        db=db,
        project_id=project_id,
        client=client,
    )

    assert result is expected_retriever

    build_v2_mock.assert_called_once_with(
        db=db,
        project_id=project_id,
        candidate_k=20,
        model=DEFAULT_RERANK_MODEL,
        max_chars_per_document=(
            DEFAULT_MAX_CHARS_PER_DOCUMENT
        ),
        client=client,
    )


@patch(
    "evals.retrieval_v3."
    "build_retrieval_v2_retriever"
)
def test_retrieval_v3_allows_candidate_override(
    build_v2_mock: MagicMock,
) -> None:
    db = MagicMock()
    project_id = uuid4()

    build_v2_mock.return_value = (
        MagicMock()
    )

    build_retrieval_v3_retriever(
        db=db,
        project_id=project_id,
        candidate_k=15,
    )

    build_v2_mock.assert_called_once_with(
        db=db,
        project_id=project_id,
        candidate_k=15,
        model=DEFAULT_RERANK_MODEL,
        max_chars_per_document=(
            DEFAULT_MAX_CHARS_PER_DOCUMENT
        ),
        client=None,
    )