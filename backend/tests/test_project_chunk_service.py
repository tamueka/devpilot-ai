import pytest

from app.services.project_chunk_service import (
    split_content_into_chunks,
)


def test_empty_content_returns_no_chunks() -> None:
    result = split_content_into_chunks(
        "",
    )

    assert result == []


def test_whitespace_content_returns_no_chunks() -> None:
    result = split_content_into_chunks(
        "   \n\n   ",
    )

    assert result == []


def test_small_content_returns_single_chunk() -> None:
    content = (
        "export const hello = 'DevPilot AI';"
    )

    result = split_content_into_chunks(
        content,
        chunk_size=100,
        chunk_overlap=10,
    )

    assert result == [content]


def test_large_content_creates_multiple_chunks() -> None:
    content = "A" * 250

    result = split_content_into_chunks(
        content,
        chunk_size=100,
        chunk_overlap=20,
    )

    assert len(result) > 1

    assert all(
        len(chunk) <= 100
        for chunk in result
    )


def test_chunks_preserve_overlap() -> None:
    content = (
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    )

    result = split_content_into_chunks(
        content,
        chunk_size=20,
        chunk_overlap=5,
    )

    assert len(result) > 1

    assert (
        result[0][-5:]
        == result[1][:5]
    )


def test_prefers_paragraph_boundary() -> None:
    content = (
        "A" * 35
        + "\n\n"
        + "B" * 35
    )

    result = split_content_into_chunks(
        content,
        chunk_size=50,
        chunk_overlap=5,
    )

    assert len(result) >= 2

    assert result[0] == (
        "A" * 35
    )


def test_prefers_line_boundary() -> None:
    content = (
        "A" * 35
        + "\n"
        + "B" * 35
    )

    result = split_content_into_chunks(
        content,
        chunk_size=50,
        chunk_overlap=5,
    )

    assert len(result) >= 2

    assert result[0] == (
        "A" * 35
    )


def test_chunk_size_must_be_positive() -> None:
    with pytest.raises(
        ValueError,
        match="chunk_size",
    ):
        split_content_into_chunks(
            "DevPilot",
            chunk_size=0,
            chunk_overlap=0,
        )


def test_overlap_cannot_be_negative() -> None:
    with pytest.raises(
        ValueError,
        match="chunk_overlap",
    ):
        split_content_into_chunks(
            "DevPilot",
            chunk_size=100,
            chunk_overlap=-1,
        )


def test_overlap_must_be_smaller_than_chunk_size() -> None:
    with pytest.raises(
        ValueError,
        match="chunk_overlap",
    ):
        split_content_into_chunks(
            "DevPilot",
            chunk_size=100,
            chunk_overlap=100,
        )


def test_chunks_are_never_empty() -> None:
    content = (
        "function hello() {\n"
        "  return 'DevPilot';\n"
        "}\n\n"
        "function goodbye() {\n"
        "  return 'Bye';\n"
        "}"
    )

    result = split_content_into_chunks(
        content,
        chunk_size=40,
        chunk_overlap=5,
    )

    assert result

    assert all(
        chunk.strip()
        for chunk in result
    )