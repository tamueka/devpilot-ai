from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from typing import Any

from google import genai
from google.genai import types

from app.ai.provider_types import (
    AIProviderConfigurationError,
    AIProviderError,
)


DEFAULT_GEMINI_EMBEDDING_MODEL = (
    "gemini-embedding-2"
)

DEFAULT_GEMINI_GENERATION_MODEL = (
    "gemini-3.5-flash-lite"
)

DEFAULT_EMBEDDING_DIMENSIONS = 1536


class GeminiProvider:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        embedding_model: str | None = None,
        generation_model: str | None = None,
        embedding_dimensions: int | None = None,
        client: Any | None = None,
    ) -> None:
        self.embedding_model = (
            embedding_model
            or os.getenv(
                "GEMINI_EMBEDDING_MODEL",
                DEFAULT_GEMINI_EMBEDDING_MODEL,
            )
        )

        self.generation_model = (
            generation_model
            or os.getenv(
                "GEMINI_GENERATION_MODEL",
                DEFAULT_GEMINI_GENERATION_MODEL,
            )
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
                "GEMINI_API_KEY",
            )
        )

        if not resolved_api_key:
            raise AIProviderConfigurationError(
                "GEMINI_API_KEY no está "
                "configurada."
            )

        self._client = genai.Client(
            api_key=resolved_api_key,
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
                "Gemini no devolvió el embedding."
            )

        return embeddings[0]

    def embed_texts(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        if not texts:
            return []

        contents = [
            types.Content(
                parts=[
                    types.Part.from_text(
                        text=text
                    )
                ]
            )
            for text in texts
        ]

        response = (
            self._client.models.embed_content(
                model=self.embedding_model,
                contents=contents,
                config=types.EmbedContentConfig(
                    output_dimensionality=(
                        self.embedding_dimensions
                    ),
                ),
            )
        )

        response_embeddings = (
            response.embeddings or []
        )

        embeddings = [
            list(
                embedding.values or []
            )
            for embedding
            in response_embeddings
        ]

        if len(embeddings) != len(texts):
            raise AIProviderError(
                "Gemini devolvió un número "
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
        config_data: dict[str, Any] = {}

        if instructions:
            config_data[
                "system_instruction"
            ] = instructions

        if max_output_tokens is not None:
            config_data[
                "max_output_tokens"
            ] = max_output_tokens

        config = (
            types.GenerateContentConfig(
                **config_data
            )
        )

        chat = self._client.chats.create(
            model=(
                model
                or self.generation_model
            ),
            config=config,
        )

        response = chat.send_message(
            prompt
        )

        content = (
            response.text or ""
        ).strip()

        if not content:
            raise AIProviderError(
                "Gemini devolvió una respuesta "
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
        # schema_name forma parte del contrato común
        # para mantener compatibilidad con OpenAI.
        _ = schema_name

        config_data: dict[str, Any] = {
            "response_mime_type": "application/json",
            "response_json_schema": dict(
                schema
            ),
        }

        if instructions:
            config_data[
                "system_instruction"
            ] = instructions

        if max_output_tokens is not None:
            config_data[
                "max_output_tokens"
            ] = max_output_tokens

        config = types.GenerateContentConfig(
            **config_data
        )

        chat = self._client.chats.create(
            model=(
                model
                or self.generation_model
            ),
            config=config,
        )

        response = chat.send_message(
            prompt
        )

        raw_content = (
            response.text or ""
        ).strip()

        if not raw_content:
            raise AIProviderError(
                "Gemini devolvió una respuesta "
                "JSON vacía."
            )

        try:
            payload = json.loads(
                raw_content
            )
        except json.JSONDecodeError as exc:
            raise AIProviderError(
                "Gemini devolvió JSON inválido."
            ) from exc

        if not isinstance(
            payload,
            dict,
        ):
            raise AIProviderError(
                "La respuesta JSON de Gemini "
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