from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.services.semantic_search_service import SemanticSearchResult
from evals.vector_candidate_retrieval import (
    build_vector_candidate_retriever,
)


def create_result(
    path: str,
    *,
    chunk_index: int,
    distance: float,
) -> SemanticSearchResult:
    return SemanticSearchResult(
        chunk_id=uuid4(),
        document_id=uuid4(),
        path=path,
        language="python",
        chunk_index=chunk_index,
        content="test content",
        distance=distance,
    )


def test_vector_candidate_retriever_requests_100_chunks_by_default() -> None:
    db = MagicMock()
    project_id = uuid4()

    with patch(
        "evals.vector_candidate_retrieval."
        "search_project_chunks",
        return_value=[],
    ) as search_mock:
        retrieve = build_vector_candidate_retriever(
            db=db,
            project_id=project_id,
        )

        retrieve(
            "pregunta",
            20,
        )

    search_mock.assert_called_once_with(
        db=db,
        project_id=project_id,
        query="pregunta",
        top_k=100,
    )


def test_vector_candidate_retriever_returns_unique_documents() -> None:
    db = MagicMock()
    project_id = uuid4()

    results = [
        create_result(
            "docs/architecture.md",
            chunk_index=1,
            distance=0.10,
        ),
        create_result(
            "docs/architecture.md",
            chunk_index=2,
            distance=0.11,
        ),
        create_result(
            "backend/app/services/rag_service.py",
            chunk_index=1,
            distance=0.12,
        ),
        create_result(
            "backend/app/services/rag_service.py",
            chunk_index=2,
            distance=0.13,
        ),
        create_result(
            "backend/app/security/auth.py",
            chunk_index=1,
            distance=0.14,
        ),
    ]

    with patch(
        "evals.vector_candidate_retrieval."
        "search_project_chunks",
        return_value=results,
    ):
        retrieve = build_vector_candidate_retriever(
            db=db,
            project_id=project_id,
        )

        retrieved = retrieve(
            "pregunta",
            20,
        )

    assert retrieved == [
        "docs/architecture.md",
        "backend/app/services/rag_service.py",
        "backend/app/security/auth.py",
    ]


def test_vector_candidate_retriever_preserves_vector_ranking() -> None:
    db = MagicMock()
    project_id = uuid4()

    results = [
        create_result(
            "first.py",
            chunk_index=1,
            distance=0.10,
        ),
        create_result(
            "second.py",
            chunk_index=1,
            distance=0.20,
        ),
        create_result(
            "third.py",
            chunk_index=1,
            distance=0.30,
        ),
    ]

    with patch(
        "evals.vector_candidate_retrieval."
        "search_project_chunks",
        return_value=results,
    ):
        retrieve = build_vector_candidate_retriever(
            db=db,
            project_id=project_id,
        )

        retrieved = retrieve(
            "pregunta",
            3,
        )

    assert retrieved == [
        "first.py",
        "second.py",
        "third.py",
    ]


def test_vector_candidate_retriever_respects_requested_document_k() -> None:
    db = MagicMock()
    project_id = uuid4()

    results = [
        create_result(
            f"file-{index}.py",
            chunk_index=1,
            distance=float(index),
        )
        for index in range(10)
    ]

    with patch(
        "evals.vector_candidate_retrieval."
        "search_project_chunks",
        return_value=results,
    ):
        retrieve = build_vector_candidate_retriever(
            db=db,
            project_id=project_id,
        )

        retrieved = retrieve(
            "pregunta",
            5,
        )

    assert len(retrieved) == 5

    assert retrieved == [
        "file-0.py",
        "file-1.py",
        "file-2.py",
        "file-3.py",
        "file-4.py",
    ]


def test_vector_candidate_retriever_normalizes_paths_for_deduplication() -> None:
    db = MagicMock()
    project_id = uuid4()

    results = [
        create_result(
            "backend/app/services/rag_service.py",
            chunk_index=1,
            distance=0.10,
        ),
        create_result(
            r"backend\app\services\rag_service.py",
            chunk_index=2,
            distance=0.11,
        ),
    ]

    with patch(
        "evals.vector_candidate_retrieval."
        "search_project_chunks",
        return_value=results,
    ):
        retrieve = build_vector_candidate_retriever(
            db=db,
            project_id=project_id,
        )

        retrieved = retrieve(
            "pregunta",
            20,
        )

    assert retrieved == [
        "backend/app/services/rag_service.py",
    ]


def test_vector_candidate_retriever_uses_k_when_larger_than_chunk_candidate_k() -> None:
    db = MagicMock()
    project_id = uuid4()

    with patch(
        "evals.vector_candidate_retrieval."
        "search_project_chunks",
        return_value=[],
    ) as search_mock:
        retrieve = build_vector_candidate_retriever(
            db=db,
            project_id=project_id,
            chunk_candidate_k=10,
        )

        retrieve(
            "pregunta",
            25,
        )

    search_mock.assert_called_once_with(
        db=db,
        project_id=project_id,
        query="pregunta",
        top_k=25,
    )


def test_vector_candidate_retriever_rejects_invalid_chunk_candidate_k() -> None:
    with pytest.raises(
        ValueError,
        match="chunk_candidate_k must be greater than zero",
    ):
        build_vector_candidate_retriever(
            db=MagicMock(),
            project_id=uuid4(),
            chunk_candidate_k=0,
        )


def test_vector_candidate_retriever_rejects_invalid_k() -> None:
    retrieve = build_vector_candidate_retriever(
        db=MagicMock(),
        project_id=uuid4(),
    )

    with pytest.raises(
        ValueError,
        match="k must be greater than zero",
    ):
        retrieve(
            "pregunta",
            0,
        )