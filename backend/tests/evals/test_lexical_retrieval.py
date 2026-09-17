from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from evals.lexical_retrieval import (
    LexicalSearchResult,
    build_lexical_retriever,
    search_project_documents_lexically,
)


def test_lexical_retriever_returns_ranked_paths() -> None:
    db = MagicMock()
    project_id = uuid4()

    results = [
        LexicalSearchResult(
            path="backend/app/security/auth.py",
            rank=0.8,
        ),
        LexicalSearchResult(
            path="backend/app/routers/auth.py",
            rank=0.6,
        ),
    ]

    with patch(
        "evals.lexical_retrieval."
        "search_project_documents_lexically",
        return_value=results,
    ) as search_mock:
        retrieve = build_lexical_retriever(
            db=db,
            project_id=project_id,
        )

        retrieved = retrieve(
            "JWT authentication",
            5,
        )

    assert retrieved == [
        "backend/app/security/auth.py",
        "backend/app/routers/auth.py",
    ]

    search_mock.assert_called_once_with(
        db=db,
        project_id=project_id,
        query="JWT authentication",
        top_k=20,
    )


def test_lexical_retriever_limits_final_results() -> None:
    db = MagicMock()
    project_id = uuid4()

    results = [
        LexicalSearchResult(
            path=f"file-{index}.py",
            rank=float(10 - index),
        )
        for index in range(10)
    ]

    with patch(
        "evals.lexical_retrieval."
        "search_project_documents_lexically",
        return_value=results,
    ):
        retrieve = build_lexical_retriever(
            db=db,
            project_id=project_id,
        )

        retrieved = retrieve(
            "authentication",
            3,
        )

    assert retrieved == [
        "file-0.py",
        "file-1.py",
        "file-2.py",
    ]


def test_lexical_retriever_uses_k_when_greater_than_candidate_k() -> None:
    db = MagicMock()
    project_id = uuid4()

    with patch(
        "evals.lexical_retrieval."
        "search_project_documents_lexically",
        return_value=[],
    ) as search_mock:
        retrieve = build_lexical_retriever(
            db=db,
            project_id=project_id,
            candidate_k=10,
        )

        retrieve(
            "query",
            25,
        )

    search_mock.assert_called_once_with(
        db=db,
        project_id=project_id,
        query="query",
        top_k=25,
    )


def test_lexical_retriever_rejects_invalid_candidate_k() -> None:
    with pytest.raises(
        ValueError,
        match="candidate_k must be greater than zero",
    ):
        build_lexical_retriever(
            db=MagicMock(),
            project_id=uuid4(),
            candidate_k=0,
        )


def test_lexical_retriever_rejects_invalid_k() -> None:
    retrieve = build_lexical_retriever(
        db=MagicMock(),
        project_id=uuid4(),
    )

    with pytest.raises(
        ValueError,
        match="k must be greater than zero",
    ):
        retrieve(
            "query",
            0,
        )


def test_lexical_search_returns_empty_for_blank_query() -> None:
    db = MagicMock()

    result = search_project_documents_lexically(
        db=db,
        project_id=uuid4(),
        query="   ",
        top_k=20,
    )

    assert result == []

    db.execute.assert_not_called()


def test_lexical_search_rejects_invalid_top_k() -> None:
    with pytest.raises(
        ValueError,
        match="top_k must be greater than zero",
    ):
        search_project_documents_lexically(
            db=MagicMock(),
            project_id=uuid4(),
            query="authentication",
            top_k=0,
        )