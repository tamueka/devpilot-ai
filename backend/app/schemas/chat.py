from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    project_id: UUID

    conversation_id: UUID | None = Field(
        default=None,
        description=(
            "Identificador de una conversación existente. "
            "Si no se envía, se crea una nueva."
        ),
    )

    message: str = Field(
        ...,
        min_length=1,
        max_length=4_000,
        description="Pregunta sobre el código del proyecto",
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Número máximo de chunks recuperados",
    )


class ChatSourceResponse(BaseModel):
    path: str
    language: str
    chunk_index: int
    excerpt: str


class ChatResponse(BaseModel):
    conversation_id: UUID
    answer: str
    sources: list[ChatSourceResponse]