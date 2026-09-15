import os
from uuid import UUID

from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Chunk, Document


EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1_536
EMBEDDING_BATCH_SIZE = 100


class EmbeddingConfigurationError(Exception):
    """Raised when the embedding provider is not configured."""


def create_project_embeddings(
    db: Session,
    project_id: UUID,
) -> int:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise EmbeddingConfigurationError(
            "OPENAI_API_KEY no está configurada.",
        )

    chunks = _get_project_chunks(
        db=db,
        project_id=project_id,
    )

    if not chunks:
        return 0

    client = OpenAI(
        api_key=api_key,
    )

    processed_chunks = 0

    for batch_start in range(
        0,
        len(chunks),
        EMBEDDING_BATCH_SIZE,
    ):
        batch = chunks[
            batch_start : batch_start + EMBEDDING_BATCH_SIZE
        ]

        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=[
                chunk.content
                for chunk in batch
            ],
            dimensions=EMBEDDING_DIMENSIONS,
        )

        if len(response.data) != len(batch):
            raise RuntimeError(
                "El número de embeddings recibidos no coincide "
                "con el número de chunks enviados.",
            )

        for chunk, embedding_data in zip(
            batch,
            response.data,
            strict=True,
        ):
            chunk.embedding = embedding_data.embedding

        processed_chunks += len(batch)

    db.flush()

    return processed_chunks


def _get_project_chunks(
    db: Session,
    project_id: UUID,
) -> list[Chunk]:
    result = db.execute(
        select(Chunk)
        .join(
            Document,
            Chunk.document_id == Document.id,
        )
        .where(
            Document.project_id == project_id,
        )
        .order_by(
            Document.path,
            Chunk.chunk_index,
        ),
    )

    return list(result.scalars().all())

def create_text_embedding(
    text: str,
) -> list[float]:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise EmbeddingConfigurationError(
            "OPENAI_API_KEY no está configurada.",
        )

    normalized_text = text.strip()

    if not normalized_text:
        raise ValueError(
            "El texto para generar el embedding no puede estar vacío.",
        )

    client = OpenAI(
        api_key=api_key,
    )

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=normalized_text,
        dimensions=EMBEDDING_DIMENSIONS,
    )

    return response.data[0].embedding