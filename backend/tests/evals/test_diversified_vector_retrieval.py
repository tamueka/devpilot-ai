from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.services.semantic_search_service import SemanticSearchResult
from evals.diversified_vector_retrieval import (
    build_diversified_vector_retriever,
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


def test_diversified_retriever_removes_duplicate_paths() -> None:
    db = MagicMock()
    project_id = uuid4()

    search_results = [
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
            "docs/demo.md",
            chunk_index=1,
            distance=0.12,
        ),
        create_result(
            "docs/demo.md",
            chunk_index=2,
            distance=0.13,
        ),
        create_result(
            "backend/app/security/resource_access.py",
            chunk_index=1,
            distance=0.14,
        ),
    ]

    with patch(
        "evals.diversified_vector_retrieval.search_project_chunks",
        return_value=search_results,
    ):
        retrieve = build_diversified_vector_retriever(
            db=db,
            project_id=project_id,
        )

        result = retrieve(
            "¿Cómo se controla el acceso?",
            5,
        )

    assert result == [
        "docs/architecture.md",
        "docs/demo.md",
        "backend/app/security/resource_access.py",
    ]


def test_diversified_retriever_preserves_original_ranking() -> None:
    db = MagicMock()
    project_id = uuid4()

    search_results = [
        create_result(
            "docs/architecture.md",
            chunk_index=1,
            distance=0.10,
        ),
        create_result(
            "backend/app/services/rag_service.py",
            chunk_index=1,
            distance=0.20,
        ),
        create_result(
            "backend/app/security/auth.py",
            chunk_index=1,
            distance=0.30,
        ),
    ]

    with patch(
        "evals.diversified_vector_retrieval.search_project_chunks",
        return_value=search_results,
    ):
        retrieve = build_diversified_vector_retriever(
            db=db,
            project_id=project_id,
        )

        result = retrieve(
            "pregunta",
            3,
        )

    assert result == [
        "docs/architecture.md",
        "backend/app/services/rag_service.py",
        "backend/app/security/auth.py",
    ]


def test_diversified_retriever_requests_twenty_candidates_by_default() -> None:
    db = MagicMock()
    project_id = uuid4()

    with patch(
        "evals.diversified_vector_retrieval.search_project_chunks",
        return_value=[],
    ) as search_mock:
        retrieve = build_diversified_vector_retriever(
            db=db,
            project_id=project_id,
        )

        retrieve(
            "pregunta",
            5,
        )

    search_mock.assert_called_once_with(
        db=db,
        project_id=project_id,
        query="pregunta",
        top_k=20,
    )


def test_diversified_retriever_uses_k_when_greater_than_candidate_k() -> None:
    db = MagicMock()
    project_id = uuid4()

    with patch(
        "evals.diversified_vector_retrieval.search_project_chunks",
        return_value=[],
    ) as search_mock:
        retrieve = build_diversified_vector_retriever(
            db=db,
            project_id=project_id,
            candidate_k=10,
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


def test_diversified_retriever_normalizes_paths_for_deduplication() -> None:
    db = MagicMock()
    project_id = uuid4()

    search_results = [
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
        "evals.diversified_vector_retrieval.search_project_chunks",
        return_value=search_results,
    ):
        retrieve = build_diversified_vector_retriever(
            db=db,
            project_id=project_id,
        )

        result = retrieve(
            "pregunta",
            5,
        )

    assert result == [
        "backend/app/services/rag_service.py",
    ]


def test_diversified_retriever_rejects_invalid_candidate_k() -> None:
    db = MagicMock()

    with pytest.raises(
        ValueError,
        match="candidate_k must be greater than zero",
    ):
        build_diversified_vector_retriever(
            db=db,
            project_id=uuid4(),
            candidate_k=0,
        )


def test_diversified_retriever_rejects_invalid_k() -> None:
    db = MagicMock()

    retrieve = build_diversified_vector_retriever(
        db=db,
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