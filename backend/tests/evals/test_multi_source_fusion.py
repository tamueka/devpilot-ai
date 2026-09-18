from __future__ import annotations

import pytest

from evals.multi_source_candidate_retrieval import (
    MultiSourceCandidates,
)
from evals.multi_source_fusion import (
    best_rank_fusion,
)


def build_candidates(
    *,
    vector: tuple[str, ...] = (),
    lexical: tuple[str, ...] = (),
    path: tuple[str, ...] = (),
) -> MultiSourceCandidates:
    union = tuple(
        dict.fromkeys(
            [
                *vector,
                *lexical,
                *path,
            ]
        )
    )

    return MultiSourceCandidates(
        vector_files=vector,
        lexical_files=lexical,
        path_files=path,
        union_files=union,
    )


def test_best_rank_is_primary_signal() -> None:
    candidates = build_candidates(
        vector=(
            "first.py",
            "strong.py",
            "consensus.py",
        ),
        lexical=(
            "other.py",
            "another.py",
            "consensus.py",
        ),
        path=(
            "path-first.py",
            "path-second.py",
            "consensus.py",
        ),
    )

    results = best_rank_fusion(
        candidates,
        final_k=10,
    )

    paths = [
        result.path
        for result in results
    ]

    assert (
        paths.index("strong.py")
        < paths.index("consensus.py")
    )


def test_consensus_breaks_equal_best_rank() -> None:
    candidates = build_candidates(
        vector=(
            "vector-first.py",
            "single.py",
            "consensus.py",
        ),
        lexical=(
            "lexical-first.py",
            "other.py",
            "consensus.py",
        ),
        path=(
            "path-first.py",
            "something.py",
            "consensus.py",
        ),
    )

    results = best_rank_fusion(
        candidates,
        final_k=10,
    )

    consensus = next(
        result
        for result in results
        if result.path == "consensus.py"
    )

    single = next(
        result
        for result in results
        if result.path == "single.py"
    )

    assert consensus.best_rank == 3
    assert consensus.source_count == 3

    assert single.best_rank == 2
    assert single.source_count == 1

    assert (
        results.index(single)
        < results.index(consensus)
    )


def test_consensus_wins_when_best_rank_is_equal() -> None:
    candidates = build_candidates(
        vector=(
            "a.py",
            "single.py",
        ),
        lexical=(
            "b.py",
            "consensus.py",
        ),
        path=(
            "c.py",
            "consensus.py",
        ),
    )

    results = best_rank_fusion(
        candidates,
        final_k=10,
    )

    paths = [
        result.path
        for result in results
    ]

    assert (
        paths.index("consensus.py")
        < paths.index("single.py")
    )


def test_fusion_tracks_source_ranks() -> None:
    candidates = build_candidates(
        vector=(
            "a.py",
            "target.py",
        ),
        lexical=(
            "target.py",
        ),
        path=(
            "x.py",
            "y.py",
            "target.py",
        ),
    )

    results = best_rank_fusion(
        candidates,
        final_k=10,
    )

    target = next(
        result
        for result in results
        if result.path == "target.py"
    )

    assert target.vector_rank == 2
    assert target.lexical_rank == 1
    assert target.path_rank == 3

    assert target.best_rank == 1
    assert target.source_count == 3
    assert target.rank_sum == 6


def test_fusion_normalizes_equivalent_paths() -> None:
    candidates = build_candidates(
        vector=(
            "src\\app\\auth.ts",
        ),
        lexical=(
            "src/app/auth.ts",
        ),
    )

    results = best_rank_fusion(
        candidates,
        final_k=10,
    )

    assert len(results) == 1

    assert (
        results[0].source_count
        == 2
    )


def test_fusion_respects_final_k() -> None:
    candidates = build_candidates(
        vector=(
            "a.py",
            "b.py",
            "c.py",
        )
    )

    results = best_rank_fusion(
        candidates,
        final_k=2,
    )

    assert len(results) == 2

    assert [
        result.path
        for result in results
    ] == [
        "a.py",
        "b.py",
    ]


def test_fusion_handles_empty_candidates() -> None:
    candidates = build_candidates()

    results = best_rank_fusion(
        candidates,
        final_k=10,
    )

    assert results == []


def test_fusion_rejects_invalid_final_k() -> None:
    candidates = build_candidates()

    with pytest.raises(
        ValueError,
        match="final_k must be greater than zero",
    ):
        best_rank_fusion(
            candidates,
            final_k=0,
        )