from __future__ import annotations

import os

from app.ai.gemini_provider import (
    GeminiProvider,
)
from app.ai.openai_provider import (
    OpenAIProvider,
)
from app.ai.provider_types import (
    EmbeddingProvider,
    GenerationProvider,
    UnsupportedAIProviderError,
)


DEFAULT_AI_PROVIDER = "openai"


def get_ai_provider_name() -> str:
    provider = os.getenv(
        "AI_PROVIDER",
        DEFAULT_AI_PROVIDER,
    )

    return provider.strip().lower()


def get_embedding_provider(
    provider_name: str | None = None,
) -> EmbeddingProvider:
    provider = _normalize_provider_name(
        provider_name
    )

    if provider == "openai":
        return OpenAIProvider()

    if provider == "gemini":
        return GeminiProvider()

    raise UnsupportedAIProviderError(
        f"Proveedor de IA no soportado: "
        f"{provider!r}."
    )


def get_generation_provider(
    provider_name: str | None = None,
) -> GenerationProvider:
    provider = _normalize_provider_name(
        provider_name
    )

    if provider == "openai":
        return OpenAIProvider()

    if provider == "gemini":
        return GeminiProvider()

    raise UnsupportedAIProviderError(
        f"Proveedor de IA no soportado: "
        f"{provider!r}."
    )


def _normalize_provider_name(
    provider_name: str | None,
) -> str:
    provider = (
        provider_name
        if provider_name is not None
        else get_ai_provider_name()
    )

    normalized = (
        provider
        .strip()
        .lower()
    )

    if not normalized:
        raise UnsupportedAIProviderError(
            "AI_PROVIDER no puede estar vacío."
        )

    return normalized
    