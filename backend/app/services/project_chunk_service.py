from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import Chunk, Document


CHUNK_SIZE = 1_000
CHUNK_OVERLAP = 150

MINIMUM_BOUNDARY_RATIO = 0.6


def create_project_chunks(
    db: Session,
    project_id: UUID,
) -> int:
    documents = _get_project_documents(
        db=db,
        project_id=project_id,
    )

    if not documents:
        return 0

    _delete_existing_chunks(
        db=db,
        documents=documents,
    )

    chunks_to_create: list[Chunk] = []

    for document in documents:
        document_chunks = split_content_into_chunks(
            document.content,
        )

        for chunk_index, content in enumerate(
            document_chunks,
        ):
            chunks_to_create.append(
                Chunk(
                    document_id=document.id,
                    chunk_index=chunk_index,
                    content=content,
                    embedding=None,
                    token_count=None,
                ),
            )

    if chunks_to_create:
        db.add_all(
            chunks_to_create,
        )

    db.flush()

    return len(
        chunks_to_create,
    )


def split_content_into_chunks(
    content: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    _validate_chunk_configuration(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    normalized_content = content.strip()

    if not normalized_content:
        return []

    if len(normalized_content) <= chunk_size:
        return [
            normalized_content,
        ]

    chunks: list[str] = []

    start = 0
    content_length = len(
        normalized_content,
    )

    while start < content_length:
        max_end = min(
            start + chunk_size,
            content_length,
        )

        end = _find_chunk_end(
            content=normalized_content,
            start=start,
            max_end=max_end,
            chunk_size=chunk_size,
        )

        chunk = normalized_content[
            start:end
        ].strip()

        if chunk:
            chunks.append(
                chunk,
            )

        if end >= content_length:
            break

        next_start = (
            end - chunk_overlap
        )

        if next_start <= start:
            next_start = end

        start = next_start

    return chunks


def _validate_chunk_configuration(
    chunk_size: int,
    chunk_overlap: int,
) -> None:
    if chunk_size <= 0:
        raise ValueError(
            "chunk_size debe ser mayor que cero.",
        )

    if chunk_overlap < 0:
        raise ValueError(
            "chunk_overlap no puede ser negativo.",
        )

    if chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap debe ser menor que chunk_size.",
        )


def _find_chunk_end(
    content: str,
    start: int,
    max_end: int,
    chunk_size: int,
) -> int:
    if max_end >= len(content):
        return len(
            content,
        )

    minimum_boundary = (
        start
        + int(
            chunk_size
            * MINIMUM_BOUNDARY_RATIO
        )
    )

    boundaries = (
        "\n\n",
        "\n",
        " ",
    )

    for boundary in boundaries:
        position = content.rfind(
            boundary,
            minimum_boundary,
            max_end,
        )

        if position != -1:
            return (
                position
                + len(boundary)
            )

    return max_end


def _get_project_documents(
    db: Session,
    project_id: UUID,
) -> list[Document]:
    result = db.execute(
        select(Document)
        .where(
            Document.project_id
            == project_id,
        )
        .order_by(
            Document.path.asc(),
        )
    )

    return list(
        result.scalars().all(),
    )


def _delete_existing_chunks(
    db: Session,
    documents: list[Document],
) -> None:
    document_ids = [
        document.id
        for document in documents
    ]

    if not document_ids:
        return

    db.execute(
        delete(Chunk).where(
            Chunk.document_id.in_(
                document_ids,
            ),
        )
    )

    db.flush()