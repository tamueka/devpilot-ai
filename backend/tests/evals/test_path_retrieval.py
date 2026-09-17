from __future__ import annotations

from unittest.mock import Mock
from uuid import uuid4

import pytest

import evals.path_retrieval as path_retrieval
from evals.path_retrieval import (
    PathSearchResult,
    build_path_retriever,
    extract_path_query_terms,
    filename_tokens,
    score_document_path,
    search_project_documents_by_path,
    split_identifier,
    tokenize_path,
)


def test_split_identifier_splits_camel_case() -> None:
    assert split_identifier(
        "ResponsePromise"
    ) == (
        "response",
        "promise",
    )


def test_split_identifier_splits_hyphens_and_underscores() -> None:
    assert split_identifier(
        "semantic_search-service"
    ) == (
        "semantic",
        "search",
        "service",
    )


def test_tokenize_path_extracts_all_segments() -> None:
    tokens = tokenize_path(
        "source/core/retry-timing.ts"
    )

    assert "source" in tokens
    assert "core" in tokens
    assert "retry" in tokens
    assert "timing" in tokens


def test_filename_tokens_ignore_directories() -> None:
    tokens = filename_tokens(
        "source/types/ResponsePromise.ts"
    )

    assert "response" in tokens
    assert "promise" in tokens
    assert "source" not in tokens
    assert "types" not in tokens


def test_extract_path_query_terms_reuses_lexical_expansions() -> None:
    terms = extract_path_query_terms(
        "¿Dónde está el servicio de autenticación?"
    )

    assert "servicio" in terms
    assert "autenticacion" in terms
    assert "auth" in terms
    assert "authentication" in terms


def test_extract_path_query_terms_expands_decoradores() -> None:
    terms = extract_path_query_terms(
        "¿Qué archivo implementa los decoradores?"
    )

    assert "decorator" in terms
    assert "decorators" in terms


def test_extract_path_query_terms_expands_testing() -> None:
    terms = extract_path_query_terms(
        "¿Qué archivo permite probar aplicaciones?"
    )

    assert "test" in terms
    assert "testing" in terms


def test_extract_path_query_terms_expands_formatting() -> None:
    terms = extract_path_query_terms(
        "¿Qué archivo se utiliza para formatear la salida?"
    )

    assert "format" in terms
    assert "formatting" in terms


def test_extract_path_query_terms_expands_utilities() -> None:
    terms = extract_path_query_terms(
        "¿Dónde están las utilidades generales?"
    )

    assert "util" in terms
    assert "utils" in terms
    assert "utility" in terms
    assert "utilities" in terms


def test_score_document_path_prefers_matching_filename() -> None:
    query = (
        "¿Qué archivo implementa "
        "los decoradores?"
    )

    decorators_score = (
        score_document_path(
            path="src/click/decorators.py",
            query=query,
        )
    )

    documentation_score = (
        score_document_path(
            path="docs/commands-and-groups.md",
            query=query,
        )
    )

    assert (
        decorators_score
        > documentation_score
    )


def test_score_document_path_prefers_source_testing_module_over_test_file() -> None:
    query = (
        "¿Qué archivo proporciona "
        "utilidades para probar aplicaciones?"
    )

    source_score = (
        score_document_path(
            path="src/click/testing.py",
            query=query,
        )
    )

    test_score = (
        score_document_path(
            path="tests/test_testing.py",
            query=query,
        )
    )

    assert source_score > test_score


def test_score_document_path_finds_formatting_module() -> None:
    score = score_document_path(
        path="src/click/formatting.py",
        query=(
            "¿Qué archivo contiene la lógica "
            "para formatear la salida?"
        ),
    )

    assert score > 0


def test_score_document_path_finds_utils_module() -> None:
    score = score_document_path(
        path="src/click/utils.py",
        query=(
            "¿Qué archivo contiene "
            "utilidades generales?"
        ),
    )

    assert score > 0


def test_score_document_path_finds_retry_timing() -> None:
    score = score_document_path(
        path="source/core/retry-timing.ts",
        query=(
            "¿Dónde está la lógica de "
            "temporización de los reintentos?"
        ),
    )

    assert score > 0


def test_search_project_documents_by_path_orders_by_score() -> None:
    db = Mock()

    scalar_result = Mock()

    scalar_result.all.return_value = [
        "docs/options.md",
        "tests/test_command_decorators.py",
        "src/click/decorators.py",
        "src/click/core.py",
    ]

    db.scalars.return_value = (
        scalar_result
    )

    results = (
        search_project_documents_by_path(
            db=db,
            project_id=uuid4(),
            query=(
                "¿Qué archivo implementa "
                "los decoradores?"
            ),
            top_k=3,
        )
    )

    assert results

    assert results[0].path == (
        "src/click/decorators.py"
    )


def test_search_project_documents_by_path_returns_only_positive_scores() -> None:
    db = Mock()

    scalar_result = Mock()

    scalar_result.all.return_value = [
        "src/example/unrelated.py",
    ]

    db.scalars.return_value = (
        scalar_result
    )

    results = (
        search_project_documents_by_path(
            db=db,
            project_id=uuid4(),
            query=(
                "decoradores"
            ),
            top_k=5,
        )
    )

    assert results == []


def test_search_project_documents_by_path_rejects_zero_top_k() -> None:
    db = Mock()

    with pytest.raises(
        ValueError,
        match="top_k must be greater than zero",
    ):
        search_project_documents_by_path(
            db=db,
            project_id=uuid4(),
            query="decoradores",
            top_k=0,
        )


def test_build_path_retriever_returns_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected_results = [
        PathSearchResult(
            path="src/click/decorators.py",
            score=10.0,
        ),
        PathSearchResult(
            path="src/click/core.py",
            score=5.0,
        ),
    ]

    def fake_search(
        *,
        db,
        project_id,
        query,
        top_k,
    ) -> list[PathSearchResult]:
        return expected_results[
            :top_k
        ]

    monkeypatch.setattr(
        path_retrieval,
        "search_project_documents_by_path",
        fake_search,
    )

    retriever = build_path_retriever(
        db=Mock(),
        project_id=uuid4(),
        candidate_k=20,
    )

    result = retriever(
        "decoradores",
        1,
    )

    assert result == [
        "src/click/decorators.py"
    ]


def test_build_path_retriever_rejects_invalid_candidate_k() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "candidate_k must be greater than zero"
        ),
    ):
        build_path_retriever(
            db=Mock(),
            project_id=uuid4(),
            candidate_k=0,
        )


def test_path_retriever_rejects_invalid_k() -> None:
    retriever = build_path_retriever(
        db=Mock(),
        project_id=uuid4(),
    )

    with pytest.raises(
        ValueError,
        match="k must be greater than zero",
    ):
        retriever(
            "decoradores",
            0,
        )