from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from typing import Any

from openai import OpenAI

from app.ai.provider_types import (
    AIProviderConfigurationError,
    AIProviderError,
)


DEFAULT_OPENAI_EMBEDDING_MODEL = (
    "text-embedding-3-small"
)

DEFAULT_OPENAI_GENERATION_MODEL = (
    "gpt-5.6-terra"
)

DEFAULT_EMBEDDING_DIMENSIONS = 1536


class OpenAIProvider:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        embedding_model: str | None = None,
        generation_model: str | None = None,
        embedding_dimensions: int | None = None,
        client: OpenAI | None = None,
    ) -> None:
        self.embedding_model = (
            embedding_model
            or os.getenv(
                "OPENAI_EMBEDDING_MODEL",
                DEFAULT_OPENAI_EMBEDDING_MODEL,
            )
        )

        self.generation_model = (
            generation_model
            or os.getenv(
                "OPENAI_GENERATION_MODEL",
            )
            or os.getenv(
                "RAG_MODEL",
            )
            or DEFAULT_OPENAI_GENERATION_MODEL
        )

        self.embedding_dimensions = (
            embedding_dimensions
            if embedding_dimensions is not None
            else int(
                os.getenv(
                    "EMBEDDING_DIMENSIONS",
                    str(
                        DEFAULT_EMBEDDING_DIMENSIONS
                    ),
                )
            )
        )

        if self.embedding_dimensions <= 0:
            raise AIProviderConfigurationError(
                "EMBEDDING_DIMENSIONS debe ser "
                "mayor que cero."
            )

        if client is not None:
            self._client = client
            return

        resolved_api_key = (
            api_key
            or os.getenv(
                "OPENAI_API_KEY",
            )
        )

        if not resolved_api_key:
            raise AIProviderConfigurationError(
                "OPENAI_API_KEY no está "
                "configurada."
            )

        self._client = OpenAI(
            api_key=resolved_api_key,
            timeout=30.0,
            max_retries=1,
        )

    def embed_text(
        self,
        text: str,
    ) -> list[float]:
        embeddings = self.embed_texts(
            [text]
        )

        if not embeddings:
            raise AIProviderError(
                "OpenAI no devolvió el embedding."
            )

        return embeddings[0]

    def embed_texts(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        if not texts:
            return []

        response = self._client.embeddings.create(
            model=self.embedding_model,
            input=list(texts),
            dimensions=self.embedding_dimensions,
        )

        embeddings = [
            list(item.embedding)
            for item in response.data
        ]

        if len(embeddings) != len(texts):
            raise AIProviderError(
                "OpenAI devolvió un número "
                "inesperado de embeddings."
            )

        self._validate_dimensions(
            embeddings
        )

        return embeddings

    def generate_text(
        self,
        *,
        prompt: str,
        instructions: str | None = None,
        model: str | None = None,
        max_output_tokens: int | None = None,
    ) -> str:
        request: dict[str, Any] = {
            "model": (
                model
                or self.generation_model
            ),
            "input": prompt,
            "store": False,
        }

        if instructions:
            request[
                "instructions"
            ] = instructions

        if max_output_tokens is not None:
            request[
                "max_output_tokens"
            ] = max_output_tokens

        response = (
            self._client.responses.create(
                **request
            )
        )

        content = (
            response.output_text or ""
        ).strip()

        if not content:
            raise AIProviderError(
                "OpenAI devolvió una respuesta "
                "vacía."
            )

        return content

    def generate_json(
        self,
        *,
        prompt: str,
        schema: Mapping[str, Any],
        schema_name: str = "response",
        instructions: str | None = None,
        model: str | None = None,
        max_output_tokens: int | None = None,
    ) -> dict[str, Any]:
        request: dict[str, Any] = {
            "model": (
                model
                or self.generation_model
            ),
            "input": prompt,
            "store": False,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "strict": True,
                    "schema": dict(schema),
                }
            },
        }

        if instructions:
            request[
                "instructions"
            ] = instructions

        if max_output_tokens is not None:
            request[
                "max_output_tokens"
            ] = max_output_tokens

        response = (
            self._client.responses.create(
                **request
            )
        )

        raw_content = (
            response.output_text or ""
        ).strip()

        if not raw_content:
            raise AIProviderError(
                "OpenAI devolvió una respuesta "
                "JSON vacía."
            )

        try:
            payload = json.loads(
                raw_content
            )
        except json.JSONDecodeError as exc:
            raise AIProviderError(
                "OpenAI devolvió JSON inválido."
            ) from exc

        if not isinstance(
            payload,
            dict,
        ):
            raise AIProviderError(
                "La respuesta JSON de OpenAI "
                "no es un objeto."
            )

        return payload

    def _validate_dimensions(
        self,
        embeddings: Sequence[
            Sequence[float]
        ],
    ) -> None:
        for embedding in embeddings:
            if (
                len(embedding)
                != self.embedding_dimensions
            ):
                raise AIProviderError(
                    "Dimensión de embedding "
                    "inesperada: "
                    f"{len(embedding)}. "
                    "Esperada: "
                    f"{self.embedding_dimensions}."
                )