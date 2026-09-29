from __future__ import annotations

import os
import time
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai import (
    AIProviderConfigurationError,
    EmbeddingProvider,
    get_ai_provider_name,
    get_embedding_provider,
)
from app.db.models import Chunk, Document


EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1_536

EMBEDDING_BATCH_SIZE = int(
    os.getenv(
        "EMBEDDING_BATCH_SIZE",
        "50",
    )
)

GEMINI_EMBEDDING_BATCH_DELAY_SECONDS = float(
    os.getenv(
        "GEMINI_EMBEDDING_BATCH_DELAY_SECONDS",
        "35",
    )
)


class EmbeddingConfigurationError(Exception):
    """Raised when the embedding provider is not configured."""


def create_project_embeddings(
    db: Session,
    project_id: UUID,
) -> int:
    if EMBEDDING_BATCH_SIZE <= 0:
        raise EmbeddingConfigurationError(
            "EMBEDDING_BATCH_SIZE debe ser mayor que cero.",
        )

    provider = _create_embedding_provider()

    provider_name = get_ai_provider_name()

    chunks = _get_project_chunks(
        db=db,
        project_id=project_id,
    )

    if not chunks:
        return 0

    processed_chunks = 0

    for batch_start in range(
        0,
        len(chunks),
        EMBEDDING_BATCH_SIZE,
    ):
        batch = chunks[
            batch_start:
            batch_start + EMBEDDING_BATCH_SIZE
        ]

        embeddings = provider.embed_texts(
            [
                chunk.content
                for chunk in batch
            ]
        )

        if len(embeddings) != len(batch):
            raise RuntimeError(
                "El número de embeddings recibidos "
                "no coincide con el número de chunks "
                "enviados.",
            )

        for chunk, embedding in zip(
            batch,
            embeddings,
            strict=True,
        ):
            if len(embedding) != EMBEDDING_DIMENSIONS:
                raise RuntimeError(
                    "El embedding recibido tiene una "
                    "dimensión incompatible. "
                    f"Esperada: {EMBEDDING_DIMENSIONS}. "
                    f"Recibida: {len(embedding)}.",
                )

            chunk.embedding = embedding

        processed_chunks += len(batch)

        if provider_name == "gemini":
            time.sleep(
                GEMINI_EMBEDDING_BATCH_DELAY_SECONDS
            )

    db.flush()

    return processed_chunks


def create_text_embedding(
    text: str,
) -> list[float]:
    normalized_text = text.strip()

    if not normalized_text:
        raise ValueError(
            "El texto para generar el embedding "
            "no puede estar vacío.",
        )

    provider = _create_embedding_provider()

    embedding = provider.embed_text(
        normalized_text,
    )

    if len(embedding) != EMBEDDING_DIMENSIONS:
        raise RuntimeError(
            "El embedding recibido tiene una "
            "dimensión incompatible. "
            f"Esperada: {EMBEDDING_DIMENSIONS}. "
            f"Recibida: {len(embedding)}.",
        )

    return embedding


def _create_embedding_provider(
) -> EmbeddingProvider:
    try:
        return get_embedding_provider()

    except (
        AIProviderConfigurationError,
        ValueError,
    ) as exc:
        raise EmbeddingConfigurationError(
            str(exc),
        ) from exc


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

    return list(
        result.scalars().all()
    )