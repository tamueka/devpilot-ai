from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from evals.hybrid_retrieval import (
    build_hybrid_retriever,
    reciprocal_rank_fusion,
)


def test_rrf_prioritizes_document_present_in_both_rankings() -> None:
    vector_files = [
        "docs/architecture.md",
        "backend/app/security/auth.py",
        "docs/api.md",
    ]

    lexical_files = [
        "backend/tests/security/test_auth.py",
        "backend/app/security/auth.py",
        "backend/app/routers/auth.py",
    ]

    results = reciprocal_rank_fusion(
        vector_files=vector_files,
        lexical_files=lexical_files,
        final_k=5,
    )

    assert results[0].path == (
        "backend/app/security/auth.py"
    )

    assert results[0].vector_rank == 2
    assert results[0].lexical_rank == 2


def test_rrf_includes_vector_only_documents() -> None:
    results = reciprocal_rank_fusion(
        vector_files=[
            "vector-only.py",
        ],
        lexical_files=[
            "lexical-only.py",
        ],
        final_k=5,
    )

    paths = [
        result.path
        for result in results
    ]

    assert "vector-only.py" in paths
    assert "lexical-only.py" in paths


def test_rrf_merges_equivalent_normalized_paths() -> None:
    results = reciprocal_rank_fusion(
        vector_files=[
            "backend/app/security/auth.py",
        ],
        lexical_files=[
            r"backend\app\security\auth.py",
        ],
        final_k=5,
    )

    assert len(results) == 1

    assert results[0].vector_rank == 1
    assert results[0].lexical_rank == 1


def test_rrf_respects_final_k() -> None:
    results = reciprocal_rank_fusion(
        vector_files=[
            "a.py",
            "b.py",
            "c.py",
        ],
        lexical_files=[
            "d.py",
            "e.py",
            "f.py",
        ],
        final_k=3,
    )

    assert len(results) == 3


def test_rrf_rejects_invalid_final_k() -> None:
    with pytest.raises(
        ValueError,
        match="final_k must be greater than zero",
    ):
        reciprocal_rank_fusion(
            vector_files=[],
            lexical_files=[],
            final_k=0,
        )


def test_rrf_rejects_invalid_rrf_k() -> None:
    with pytest.raises(
        ValueError,
        match="rrf_k must be greater than zero",
    ):
        reciprocal_rank_fusion(
            vector_files=[],
            lexical_files=[],
            final_k=5,
            rrf_k=0,
        )


def test_hybrid_retriever_combines_vector_and_lexical_results() -> None:
    db = MagicMock()
    project_id = uuid4()

    vector_results = [
        "docs/architecture.md",
        "backend/app/security/auth.py",
        "docs/api.md",
    ]

    lexical_results = [
        "backend/tests/security/test_auth.py",
        "backend/app/security/auth.py",
        "backend/app/routers/auth.py",
    ]

    with (
        patch(
            "evals.hybrid_retrieval."
            "build_diversified_vector_retriever"
        ) as vector_builder,
        patch(
            "evals.hybrid_retrieval."
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

        retrieve = build_hybrid_retriever(
            db=db,
            project_id=project_id,
            vector_candidate_k=20,
            lexical_candidate_k=20,
        )

        result = retrieve(
            "¿Cómo funciona la autenticación?",
            5,
        )

    assert result[0] == (
        "backend/app/security/auth.py"
    )

    vector_retrieve.assert_called_once_with(
        "¿Cómo funciona la autenticación?",
        20,
    )

    lexical_retrieve.assert_called_once_with(
        "¿Cómo funciona la autenticación?",
        20,
    )


def test_hybrid_retriever_rejects_invalid_k() -> None:
    db = MagicMock()
    project_id = uuid4()

    with (
        patch(
            "evals.hybrid_retrieval."
            "build_diversified_vector_retriever",
            return_value=MagicMock(),
        ),
        patch(
            "evals.hybrid_retrieval."
            "build_lexical_retriever",
            return_value=MagicMock(),
        ),
    ):
        retrieve = build_hybrid_retriever(
            db=db,
            project_id=project_id,
        )

        with pytest.raises(
            ValueError,
            match="k must be greater than zero",
        ):
            retrieve(
                "query",
                0,
            )


@pytest.mark.parametrize(
    (
        "vector_candidate_k",
        "lexical_candidate_k",
        "rrf_k",
        "expected_message",
    ),
    [
        (
            0,
            20,
            60,
            "vector_candidate_k must be greater than zero",
        ),
        (
            20,
            0,
            60,
            "lexical_candidate_k must be greater than zero",
        ),
        (
            20,
            20,
            0,
            "rrf_k must be greater than zero",
        ),
    ],
)


def test_hybrid_retriever_rejects_invalid_configuration(
    vector_candidate_k: int,
    lexical_candidate_k: int,
    rrf_k: int,
    expected_message: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=expected_message,
    ):
        build_hybrid_retriever(
            db=MagicMock(),
            project_id=uuid4(),
            vector_candidate_k=vector_candidate_k,
            lexical_candidate_k=lexical_candidate_k,
            rrf_k=rrf_k,
        )


def test_rrf_vector_weight_can_prioritize_vector_result() -> None:
    results = reciprocal_rank_fusion(
        vector_files=[
            "vector.py",
            "shared.py",
        ],
        lexical_files=[
            "lexical.py",
            "shared.py",
        ],
        final_k=3,
        vector_weight=2.0,
        lexical_weight=1.0,
    )

    assert results[0].path == "shared.py"

    vector_only = next(
        result
        for result in results
        if result.path == "vector.py"
    )

    lexical_only = next(
        result
        for result in results
        if result.path == "lexical.py"
    )

    assert vector_only.score > lexical_only.score


def test_rrf_lexical_weight_can_prioritize_lexical_result() -> None:
    results = reciprocal_rank_fusion(
        vector_files=[
            "vector.py",
        ],
        lexical_files=[
            "lexical.py",
        ],
        final_k=2,
        vector_weight=1.0,
        lexical_weight=2.0,
    )

    assert results[0].path == "lexical.py"


@pytest.mark.parametrize(
    (
        "vector_weight",
        "lexical_weight",
        "expected_message",
    ),
    [
        (
            0.0,
            1.0,
            "vector_weight must be greater than zero",
        ),
        (
            1.0,
            0.0,
            "lexical_weight must be greater than zero",
        ),
    ],
)
def test_rrf_rejects_invalid_weights(
    vector_weight: float,
    lexical_weight: float,
    expected_message: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=expected_message,
    ):
        reciprocal_rank_fusion(
            vector_files=[],
            lexical_files=[],
            final_k=5,
            vector_weight=vector_weight,
            lexical_weight=lexical_weight,
        )