from __future__ import annotations

from unittest.mock import Mock
from uuid import uuid4

import pytest

import evals.multi_source_candidate_retrieval as module
from evals.multi_source_candidate_retrieval import (
    MultiSourceCandidates,
    build_multi_source_candidate_collector,
    merge_unique_paths,
)


def test_merge_unique_paths_combines_sources() -> None:
    result = merge_unique_paths(
        (
            "src/a.py",
            "src/b.py",
        ),
        (
            "src/c.py",
        ),
        (
            "src/d.py",
        ),
    )

    assert result == (
        "src/a.py",
        "src/b.py",
        "src/c.py",
        "src/d.py",
    )


def test_merge_unique_paths_removes_duplicates() -> None:
    result = merge_unique_paths(
        (
            "src/a.py",
            "src/b.py",
        ),
        (
            "src/b.py",
            "src/c.py",
        ),
        (
            "src/a.py",
            "src/d.py",
        ),
    )

    assert result == (
        "src/a.py",
        "src/b.py",
        "src/c.py",
        "src/d.py",
    )


def test_merge_unique_paths_normalizes_paths() -> None:
    result = merge_unique_paths(
        (
            "src\\app\\auth.ts",
        ),
        (
            "src/app/auth.ts",
        ),
    )

    assert result == (
        "src\\app\\auth.ts",
    )


def test_collector_preserves_individual_rankings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    vector_retrieve = Mock(
        return_value=[
            "vector-1.py",
            "shared.py",
        ]
    )

    lexical_retrieve = Mock(
        return_value=[
            "lexical-1.py",
            "shared.py",
        ]
    )

    path_retrieve = Mock(
        return_value=[
            "path-1.py",
            "shared.py",
        ]
    )

    monkeypatch.setattr(
        module,
        "build_vector_candidate_retriever",
        Mock(
            return_value=vector_retrieve
        ),
    )

    monkeypatch.setattr(
        module,
        "build_lexical_retriever",
        Mock(
            return_value=lexical_retrieve
        ),
    )

    monkeypatch.setattr(
        module,
        "build_path_retriever",
        Mock(
            return_value=path_retrieve
        ),
    )

    collector = (
        build_multi_source_candidate_collector(
            db=Mock(),
            project_id=uuid4(),
        )
    )

    result = collector(
        "Where is authentication implemented?"
    )

    assert isinstance(
        result,
        MultiSourceCandidates,
    )

    assert result.vector_files == (
        "vector-1.py",
        "shared.py",
    )

    assert result.lexical_files == (
        "lexical-1.py",
        "shared.py",
    )

    assert result.path_files == (
        "path-1.py",
        "shared.py",
    )


def test_collector_builds_unique_union(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        module,
        "build_vector_candidate_retriever",
        Mock(
            return_value=Mock(
                return_value=[
                    "src/a.py",
                    "src/common.py",
                ]
            )
        ),
    )

    monkeypatch.setattr(
        module,
        "build_lexical_retriever",
        Mock(
            return_value=Mock(
                return_value=[
                    "src/b.py",
                    "src/common.py",
                ]
            )
        ),
    )

    monkeypatch.setattr(
        module,
        "build_path_retriever",
        Mock(
            return_value=Mock(
                return_value=[
                    "src/c.py",
                    "src/common.py",
                ]
            )
        ),
    )

    collector = (
        build_multi_source_candidate_collector(
            db=Mock(),
            project_id=uuid4(),
        )
    )

    result = collector(
        "test question"
    )

    assert result.union_files == (
        "src/a.py",
        "src/common.py",
        "src/b.py",
        "src/c.py",
    )


def test_collector_uses_configured_candidate_sizes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    vector_retrieve = Mock(
        return_value=[]
    )

    lexical_retrieve = Mock(
        return_value=[]
    )

    path_retrieve = Mock(
        return_value=[]
    )

    vector_builder = Mock(
        return_value=vector_retrieve
    )

    lexical_builder = Mock(
        return_value=lexical_retrieve
    )

    path_builder = Mock(
        return_value=path_retrieve
    )

    monkeypatch.setattr(
        module,
        "build_vector_candidate_retriever",
        vector_builder,
    )

    monkeypatch.setattr(
        module,
        "build_lexical_retriever",
        lexical_builder,
    )

    monkeypatch.setattr(
        module,
        "build_path_retriever",
        path_builder,
    )

    db = Mock()
    project_id = uuid4()

    collector = (
        build_multi_source_candidate_collector(
            db=db,
            project_id=project_id,
            vector_document_k=15,
            lexical_document_k=12,
            path_document_k=8,
            chunk_candidate_k=150,
        )
    )

    collector(
        "test question"
    )

    vector_builder.assert_called_once_with(
        db=db,
        project_id=project_id,
        chunk_candidate_k=150,
    )

    lexical_builder.assert_called_once_with(
        db=db,
        project_id=project_id,
        candidate_k=12,
    )

    path_builder.assert_called_once_with(
        db=db,
        project_id=project_id,
        candidate_k=8,
    )

    vector_retrieve.assert_called_once_with(
        "test question",
        15,
    )

    lexical_retrieve.assert_called_once_with(
        "test question",
        12,
    )

    path_retrieve.assert_called_once_with(
        "test question",
        8,
    )


@pytest.mark.parametrize(
    (
        "parameter",
        "value",
        "message",
    ),
    [
        (
            "vector_document_k",
            0,
            (
                "vector_document_k "
                "must be greater than zero"
            ),
        ),
        (
            "lexical_document_k",
            0,
            (
                "lexical_document_k "
                "must be greater than zero"
            ),
        ),
        (
            "path_document_k",
            0,
            (
                "path_document_k "
                "must be greater than zero"
            ),
        ),
        (
            "chunk_candidate_k",
            0,
            (
                "chunk_candidate_k "
                "must be greater than zero"
            ),
        ),
    ],
)
def test_collector_rejects_invalid_configuration(
    parameter: str,
    value: int,
    message: str,
) -> None:
    kwargs = {
        "vector_document_k": 20,
        "lexical_document_k": 20,
        "path_document_k": 20,
        "chunk_candidate_k": 100,
    }

    kwargs[
        parameter
    ] = value

    with pytest.raises(
        ValueError,
        match=message,
    ):
        build_multi_source_candidate_collector(
            db=Mock(),
            project_id=uuid4(),
            **kwargs,
        )


def test_collector_rejects_blank_question(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        module,
        "build_vector_candidate_retriever",
        Mock(
            return_value=Mock()
        ),
    )

    monkeypatch.setattr(
        module,
        "build_lexical_retriever",
        Mock(
            return_value=Mock()
        ),
    )

    monkeypatch.setattr(
        module,
        "build_path_retriever",
        Mock(
            return_value=Mock()
        ),
    )

    collector = (
        build_multi_source_candidate_collector(
            db=Mock(),
            project_id=uuid4(),
        )
    )

    with pytest.raises(
        ValueError,
        match="question must not be blank",
    ):
        collector(
            "   "
        )