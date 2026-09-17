from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from evals.reranking_candidate_retrieval import (
    build_reranking_candidate_retriever,
)


def test_candidate_retriever_combines_vector_and_lexical_rankings() -> None:
    db = MagicMock()
    project_id = uuid4()

    vector_results = [
        "vector-a.py",
        "shared.py",
        "vector-b.py",
    ]

    lexical_results = [
        "lexical-a.py",
        "shared.py",
        "lexical-b.py",
    ]

    with (
        patch(
            "evals.reranking_candidate_retrieval."
            "build_vector_candidate_retriever"
        ) as vector_builder,
        patch(
            "evals.reranking_candidate_retrieval."
            "build_lexical_retriever"
        ) as lexical_builder,
    ):
        vector_retrieve = MagicMock(
            return_value=vector_results
        )

        lexical_retrieve = MagicMock(
            return_value=lexical_results
        )

        vector_builder.return_value = (
            vector_retrieve
        )

        lexical_builder.return_value = (
            lexical_retrieve
        )

        retrieve = build_reranking_candidate_retriever(
            db=db,
            project_id=project_id,
        )

        result = retrieve(
            "pregunta",
            5,
        )

    assert result[0] == "shared.py"

    vector_retrieve.assert_called_once_with(
        "pregunta",
        20,
    )

    lexical_retrieve.assert_called_once_with(
        "pregunta",
        20,
    )


def test_candidate_retriever_returns_at_most_requested_k() -> None:
    db = MagicMock()
    project_id = uuid4()

    vector_results = [
        f"vector-{index}.py"
        for index in range(20)
    ]

    lexical_results = [
        f"lexical-{index}.py"
        for index in range(20)
    ]

    with (
        patch(
            "evals.reranking_candidate_retrieval."
            "build_vector_candidate_retriever",
            return_value=MagicMock(
                return_value=vector_results
            ),
        ),
        patch(
            "evals.reranking_candidate_retrieval."
            "build_lexical_retriever",
            return_value=MagicMock(
                return_value=lexical_results
            ),
        ),
    ):
        retrieve = build_reranking_candidate_retriever(
            db=db,
            project_id=project_id,
        )

        result = retrieve(
            "pregunta",
            10,
        )

    assert len(result) == 10


def test_candidate_retriever_rejects_invalid_requested_k() -> None:
    with (
        patch(
            "evals.reranking_candidate_retrieval."
            "build_vector_candidate_retriever",
            return_value=MagicMock(),
        ),
        patch(
            "evals.reranking_candidate_retrieval."
            "build_lexical_retriever",
            return_value=MagicMock(),
        ),
    ):
        retrieve = build_reranking_candidate_retriever(
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


@pytest.mark.parametrize(
    (
        "argument",
        "value",
        "expected_message",
    ),
    [
        (
            "vector_document_k",
            0,
            "vector_document_k must be greater than zero",
        ),
        (
            "lexical_document_k",
            0,
            "lexical_document_k must be greater than zero",
        ),
        (
            "chunk_candidate_k",
            0,
            "chunk_candidate_k must be greater than zero",
        ),
        (
            "rrf_k",
            0,
            "rrf_k must be greater than zero",
        ),
        (
            "vector_weight",
            0.0,
            "vector_weight must be greater than zero",
        ),
        (
            "lexical_weight",
            0.0,
            "lexical_weight must be greater than zero",
        ),
    ],
)
def test_candidate_retriever_rejects_invalid_configuration(
    argument: str,
    value: int | float,
    expected_message: str,
) -> None:
    kwargs = {
        argument: value,
    }

    with pytest.raises(
        ValueError,
        match=expected_message,
    ):
        build_reranking_candidate_retriever(
            db=MagicMock(),
            project_id=uuid4(),
            **kwargs,
        )