from unittest.mock import MagicMock
from uuid import uuid4

from app.db.models import Conversation, Message
from app.services.conversation_service import (
    MAX_CONVERSATION_TITLE_LENGTH,
    create_conversation,
    get_conversation,
    save_assistant_message,
    save_user_message,
)


def test_create_conversation() -> None:
    db = MagicMock()
    project_id = uuid4()

    conversation = create_conversation(
        db=db,
        project_id=project_id,
        first_message="¿Qué arquitectura utiliza este proyecto?",
    )

    assert isinstance(
        conversation,
        Conversation,
    )

    assert (
        conversation.project_id
        == project_id
    )

    assert conversation.title == (
        "¿Qué arquitectura utiliza este proyecto?"
    )

    db.add.assert_called_once_with(
        conversation,
    )

    db.flush.assert_called_once()


def test_create_conversation_normalizes_title_whitespace() -> None:
    db = MagicMock()

    conversation = create_conversation(
        db=db,
        project_id=uuid4(),
        first_message=(
            "¿Qué   arquitectura\n"
            "utiliza\teste proyecto?"
        ),
    )

    assert conversation.title == (
        "¿Qué arquitectura utiliza este proyecto?"
    )


def test_create_conversation_truncates_long_title() -> None:
    db = MagicMock()

    first_message = (
        "A"
        * (
            MAX_CONVERSATION_TITLE_LENGTH
            + 50
        )
    )

    conversation = create_conversation(
        db=db,
        project_id=uuid4(),
        first_message=first_message,
    )

    assert conversation.title is not None

    assert len(
        conversation.title,
    ) == MAX_CONVERSATION_TITLE_LENGTH

    assert conversation.title.endswith(
        "...",
    )


def test_get_conversation_uses_session_get() -> None:
    db = MagicMock()

    conversation_id = uuid4()

    expected_conversation = MagicMock(
        spec=Conversation,
    )

    db.get.return_value = (
        expected_conversation
    )

    result = get_conversation(
        db=db,
        conversation_id=conversation_id,
    )

    assert (
        result
        is expected_conversation
    )

    db.get.assert_called_once_with(
        Conversation,
        conversation_id,
    )


def test_save_user_message() -> None:
    db = MagicMock()

    conversation_id = uuid4()

    message = save_user_message(
        db=db,
        conversation_id=conversation_id,
        content="¿Qué hace este archivo?",
    )

    assert isinstance(
        message,
        Message,
    )

    assert (
        message.conversation_id
        == conversation_id
    )

    assert message.role == "user"

    assert (
        message.content
        == "¿Qué hace este archivo?"
    )

    assert message.sources is None

    db.add.assert_called_once_with(
        message,
    )

    db.flush.assert_called_once()


def test_save_assistant_message() -> None:
    db = MagicMock()

    conversation_id = uuid4()

    sources = [
        {
            "path": "src/app/app.ts",
            "language": "typescript",
            "chunk_index": 0,
            "excerpt": "export class App {}",
        },
    ]

    message = save_assistant_message(
        db=db,
        conversation_id=conversation_id,
        content="El archivo define la clase App.",
        sources=sources,
    )

    assert isinstance(
        message,
        Message,
    )

    assert (
        message.conversation_id
        == conversation_id
    )

    assert message.role == "assistant"

    assert message.content == (
        "El archivo define la clase App."
    )

    assert message.sources == sources

    db.add.assert_called_once_with(
        message,
    )

    db.flush.assert_called_once()