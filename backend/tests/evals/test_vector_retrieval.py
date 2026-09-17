from unittest.mock import MagicMock, patch
from uuid import uuid4

from evals.vector_retrieval import build_vector_retriever
from app.services.semantic_search_service import SemanticSearchResult


def test_vector_retriever_returns_paths_in_retrieval_order() -> None:
    db = MagicMock()
    project_id = uuid4()

    search_results = [
        SemanticSearchResult(
            chunk_id=uuid4(),
            document_id=uuid4(),
            path="backend/app/services/rag_service.py",
            language="python",
            chunk_index=2,
            content="rag content",
            distance=0.10,
        ),
        SemanticSearchResult(
            chunk_id=uuid4(),
            document_id=uuid4(),
            path="backend/app/services/conversation_service.py",
            language="python",
            chunk_index=1,
            content="conversation content",
            distance=0.20,
        ),
    ]

    with patch(
        "evals.vector_retrieval.search_project_chunks",
        return_value=search_results,
    ) as search_mock:
        retrieve = build_vector_retriever(
            db=db,
            project_id=project_id,
        )

        result = retrieve(
            "¿Cómo funciona el historial?",
            5,
        )

    assert result == [
        "backend/app/services/rag_service.py",
        "backend/app/services/conversation_service.py",
    ]

    search_mock.assert_called_once_with(
        db=db,
        project_id=project_id,
        query="¿Cómo funciona el historial?",
        top_k=5,
    )


def test_vector_retriever_preserves_duplicate_document_paths() -> None:
    db = MagicMock()
    project_id = uuid4()

    duplicated_path = "backend/app/services/rag_service.py"

    search_results = [
        SemanticSearchResult(
            chunk_id=uuid4(),
            document_id=uuid4(),
            path=duplicated_path,
            language="python",
            chunk_index=1,
            content="first chunk",
            distance=0.10,
        ),
        SemanticSearchResult(
            chunk_id=uuid4(),
            document_id=uuid4(),
            path=duplicated_path,
            language="python",
            chunk_index=2,
            content="second chunk",
            distance=0.12,
        ),
    ]

    with patch(
        "evals.vector_retrieval.search_project_chunks",
        return_value=search_results,
    ):
        retrieve = build_vector_retriever(
            db=db,
            project_id=project_id,
        )

        result = retrieve(
            "¿Cómo funciona RAG?",
            5,
        )

    assert result == [
        duplicated_path,
        duplicated_path,
    ]