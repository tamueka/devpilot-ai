from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol, runtime_checkable


class AIProviderError(RuntimeError):
    """Error base de los proveedores de IA."""


class AIProviderConfigurationError(
    AIProviderError
):
    """Configuración inválida o incompleta."""


class UnsupportedAIProviderError(
    AIProviderConfigurationError
):
    """Proveedor de IA no soportado."""


@runtime_checkable
class EmbeddingProvider(Protocol):
    def embed_text(
        self,
        text: str,
    ) -> list[float]:
        ...

    def embed_texts(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        ...


@runtime_checkable
class GenerationProvider(Protocol):
    def generate_text(
        self,
        *,
        prompt: str,
        instructions: str | None = None,
        model: str | None = None,
        max_output_tokens: int | None = None,
    ) -> str:
        ...

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
        ...