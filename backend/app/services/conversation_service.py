from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Conversation, Message


MAX_CONVERSATION_TITLE_LENGTH = 120


def create_conversation(
    db: Session,
    project_id: UUID,
    first_message: str,
) -> Conversation:
    conversation = Conversation(
        project_id=project_id,
        title=_create_conversation_title(
            first_message,
        ),
    )

    db.add(conversation)
    db.flush()

    return conversation


def get_project_conversations(
    db: Session,
    project_id: UUID,
) -> list[Conversation]:
    result = db.execute(
        select(Conversation)
        .where(
            Conversation.project_id == project_id,
        )
        .order_by(
            Conversation.created_at.desc(),
        ),
    )

    return list(
        result.scalars().all(),
    )


def get_conversation(
    db: Session,
    conversation_id: UUID,
) -> Conversation | None:
    return db.get(
        Conversation,
        conversation_id,
    )


def get_conversation_messages(
    db: Session,
    conversation_id: UUID,
) -> list[Message]:
    result = db.execute(
        select(Message)
        .where(
            Message.conversation_id == conversation_id,
        )
        .order_by(
            Message.created_at.asc(),
        ),
    )

    return list(
        result.scalars().all(),
    )


def save_user_message(
    db: Session,
    conversation_id: UUID,
    content: str,
) -> Message:
    return _save_message(
        db=db,
        conversation_id=conversation_id,
        role="user",
        content=content,
        sources=None,
    )


def save_assistant_message(
    db: Session,
    conversation_id: UUID,
    content: str,
    sources: list[dict[str, Any]],
) -> Message:
    return _save_message(
        db=db,
        conversation_id=conversation_id,
        role="assistant",
        content=content,
        sources=sources,
    )


def _save_message(
    db: Session,
    conversation_id: UUID,
    role: str,
    content: str,
    sources: list[dict[str, Any]] | None,
) -> Message:
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        sources=sources,
    )

    db.add(message)
    db.flush()

    return message


def _create_conversation_title(
    first_message: str,
) -> str:
    normalized_message = " ".join(
        first_message.split(),
    )

    if (
        len(normalized_message)
        <= MAX_CONVERSATION_TITLE_LENGTH
    ):
        return normalized_message

    return (
        normalized_message[
            :MAX_CONVERSATION_TITLE_LENGTH - 3
        ].rstrip()
        + "..."
    )