from io import BytesIO
from pathlib import Path
import pytest
from app.security.upload_size import (
    UploadTooLargeError,
    copy_stream_with_size_limit,
    save_stream_with_size_limit,
)


def test_copies_file_below_size_limit() -> None:
    source = BytesIO(
        b"DevPilot",
    )

    destination = BytesIO()

    copied_bytes = (
        copy_stream_with_size_limit(
            source=source,
            destination=destination,
            max_bytes=100,
            chunk_size=4,
        )
    )

    assert copied_bytes == 8

    assert (
        destination.getvalue()
        == b"DevPilot"
    )


def test_accepts_file_exactly_at_limit() -> None:
    source = BytesIO(
        b"A" * 10,
    )

    destination = BytesIO()

    copied_bytes = (
        copy_stream_with_size_limit(
            source=source,
            destination=destination,
            max_bytes=10,
            chunk_size=4,
        )
    )

    assert copied_bytes == 10

    assert len(
        destination.getvalue(),
    ) == 10


def test_rejects_file_above_limit() -> None:
    source = BytesIO(
        b"A" * 11,
    )

    destination = BytesIO()

    with pytest.raises(
        UploadTooLargeError,
        match="tamaño máximo",
    ):
        copy_stream_with_size_limit(
            source=source,
            destination=destination,
            max_bytes=10,
            chunk_size=4,
        )


def test_rejects_invalid_max_size() -> None:
    with pytest.raises(
        ValueError,
        match="max_bytes",
    ):
        copy_stream_with_size_limit(
            source=BytesIO(b"data"),
            destination=BytesIO(),
            max_bytes=0,
        )


def test_rejects_invalid_chunk_size() -> None:
    with pytest.raises(
        ValueError,
        match="chunk_size",
    ):
        copy_stream_with_size_limit(
            source=BytesIO(b"data"),
            destination=BytesIO(),
            max_bytes=100,
            chunk_size=0,
        )


def test_removes_partial_file_when_upload_is_too_large(
    tmp_path: Path,
) -> None:
    destination = (
        tmp_path
        / "project.zip"
    )

    source = BytesIO(
        b"A" * 20,
    )

    with pytest.raises(
        UploadTooLargeError,
    ):
        save_stream_with_size_limit(
            source=source,
            destination_path=destination,
            max_bytes=10,
        )

    assert not destination.exists()


def test_saves_valid_file_to_disk(
    tmp_path: Path,
) -> None:
    destination = (
        tmp_path
        / "projects"
        / "project.zip"
    )

    source = BytesIO(
        b"valid zip content",
    )

    copied_bytes = (
        save_stream_with_size_limit(
            source=source,
            destination_path=destination,
            max_bytes=100,
        )
    )

    assert destination.exists()

    assert (
        destination.read_bytes()
        == b"valid zip content"
    )

    assert copied_bytes == len(
        b"valid zip content",
    )