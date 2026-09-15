from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ConversationResponse(BaseModel):
    id: UUID
    project_id: UUID
    title: str | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    sources: list[dict[str, Any]] | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class ConversationDetailResponse(
    ConversationResponse,
):
    messages: list[MessageResponse]