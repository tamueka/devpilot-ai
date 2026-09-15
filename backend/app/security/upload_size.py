from pathlib import Path
from typing import BinaryIO


MAX_UPLOAD_SIZE_BYTES = (
    50 * 1024 * 1024
)

UPLOAD_CHUNK_SIZE = (
    1024 * 1024
)


class UploadTooLargeError(
    ValueError,
):
    pass


def copy_stream_with_size_limit(
    source: BinaryIO,
    destination: BinaryIO,
    *,
    max_bytes: int = MAX_UPLOAD_SIZE_BYTES,
    chunk_size: int = UPLOAD_CHUNK_SIZE,
) -> int:
    if max_bytes <= 0:
        raise ValueError(
            "max_bytes debe ser mayor que cero.",
        )

    if chunk_size <= 0:
        raise ValueError(
            "chunk_size debe ser mayor que cero.",
        )

    total_bytes = 0

    while True:
        chunk = source.read(
            chunk_size,
        )

        if not chunk:
            break

        total_bytes += len(
            chunk,
        )

        if total_bytes > max_bytes:
            raise UploadTooLargeError(
                "El archivo ZIP supera "
                "el tamaño máximo permitido.",
            )

        destination.write(
            chunk,
        )

    return total_bytes


def save_stream_with_size_limit(
    source: BinaryIO,
    destination_path: Path,
    *,
    max_bytes: int = MAX_UPLOAD_SIZE_BYTES,
) -> int:
    destination_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        with destination_path.open(
            "wb",
        ) as destination:
            return copy_stream_with_size_limit(
                source=source,
                destination=destination,
                max_bytes=max_bytes,
            )

    except Exception:
        destination_path.unlink(
            missing_ok=True,
        )
        raise