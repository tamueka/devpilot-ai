from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

import app.routers.chat as chat_router_module

from app.services.project_embedding_service import (
    EmbeddingConfigurationError,
)
from app.services.rag_service import (
    RagResult,
    RagSource,
)


@pytest.fixture
def db_mock() -> MagicMock:
    return MagicMock()


@pytest.fixture
def current_user():
    return SimpleNamespace(
        id=uuid4(),
        email="test@example.com",
        is_active=True,
    )


@pytest.fixture
def client(
    db_mock: MagicMock,
    current_user,
) -> TestClient:
    test_app = FastAPI()

    test_app.include_router(
        chat_router_module.router,
    )

    def override_get_db():
        yield db_mock

    def override_current_user():
        return current_user

    def override_chat_rate_limit():
        return None

    test_app.dependency_overrides[
        chat_router_module.get_db
    ] = override_get_db

    test_app.dependency_overrides[
        chat_router_module.get_current_user
    ] = override_current_user

    test_app.dependency_overrides[
        chat_router_module.enforce_chat_rate_limit
    ] = override_chat_rate_limit

    return TestClient(
        test_app,
    )


def test_chat_creates_new_conversation(
    client: TestClient,
    db_mock: MagicMock,
    current_user,
) -> None:
    project_id = uuid4()
    conversation_id = uuid4()

    project = SimpleNamespace(
        id=project_id,
        owner_id=current_user.id,
        status="INDEXED",
    )

    conversation = SimpleNamespace(
        id=conversation_id,
        project_id=project_id,
    )

    rag_result = RagResult(
        answer=(
            "La aplicación utiliza Angular."
        ),
        sources=[
            RagSource(
                path="src/app/app.ts",
                language="typescript",
                chunk_index=0,
                excerpt=(
                    "export class App {}"
                ),
            ),
        ],
    )

    db_mock.get.return_value = project

    with (
        patch(
            "app.routers.chat."
            "create_conversation",
            return_value=conversation,
        ) as create_conversation_mock,
        patch(
            "app.routers.chat."
            "save_user_message",
        ) as save_user_message_mock,
        patch(
            "app.routers.chat."
            "answer_project_question",
            return_value=rag_result,
        ) as rag_mock,
        patch(
            "app.routers.chat."
            "save_assistant_message",
        ) as save_assistant_message_mock,
    ):
        response = client.post(
            "/chat",
            json={
                "project_id": str(
                    project_id,
                ),
                "message": (
                    "¿Qué tecnología utiliza?"
                ),
                "top_k": 5,
            },
        )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data[
        "conversation_id"
    ] == str(
        conversation_id,
    )

    assert response_data[
        "answer"
    ] == (
        "La aplicación utiliza Angular."
    )

    assert len(
        response_data["sources"],
    ) == 1

    assert response_data[
        "sources"
    ][0]["path"] == (
        "src/app/app.ts"
    )

    create_conversation_mock.assert_called_once()

    save_user_message_mock.assert_called_once()

    rag_mock.assert_called_once()

    save_assistant_message_mock.assert_called_once()

    db_mock.commit.assert_called_once()


def test_chat_continues_existing_conversation_with_history(
    client: TestClient,
    db_mock: MagicMock,
    current_user,
) -> None:
    project_id = uuid4()
    conversation_id = uuid4()

    project = SimpleNamespace(
        id=project_id,
        owner_id=current_user.id,
        status="INDEXED",
    )

    conversation = SimpleNamespace(
        id=conversation_id,
        project_id=project_id,
    )

    previous_messages = [
        SimpleNamespace(
            role="user",
            content=(
                "¿Cómo se llama la constante?"
            ),
        ),
        SimpleNamespace(
            role="assistant",
            content=(
                "La constante se llama hello."
            ),
        ),
    ]

    rag_result = RagResult(
        answer=(
            "Su valor es `DevPilot AI`."
        ),
        sources=[
            RagSource(
                path="src/app/app.ts",
                language="typescript",
                chunk_index=0,
                excerpt=(
                    "export const hello = "
                    "'DevPilot AI';"
                ),
            ),
        ],
    )

    db_mock.get.return_value = project

    with (
        patch(
            "app.routers.chat."
            "get_conversation_for_project",
            return_value=conversation,
        ) as get_conversation_mock,
        patch(
            "app.routers.chat."
            "get_conversation_messages",
            return_value=previous_messages,
        ) as get_messages_mock,
        patch(
            "app.routers.chat."
            "save_user_message",
        ) as save_user_message_mock,
        patch(
            "app.routers.chat."
            "answer_project_question",
            return_value=rag_result,
        ) as rag_mock,
        patch(
            "app.routers.chat."
            "save_assistant_message",
        ) as save_assistant_message_mock,
    ):
        response = client.post(
            "/chat",
            json={
                "project_id": str(
                    project_id,
                ),
                "conversation_id": str(
                    conversation_id,
                ),
                "message": (
                    "¿Y cuál es su valor?"
                ),
                "top_k": 5,
            },
        )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data[
        "conversation_id"
    ] == str(
        conversation_id,
    )

    assert response_data[
        "answer"
    ] == (
        "Su valor es `DevPilot AI`."
    )

    get_conversation_mock.assert_called_once_with(
        db=db_mock,
        conversation_id=conversation_id,
        project_id=project_id,
    )

    get_messages_mock.assert_called_once_with(
        db=db_mock,
        conversation_id=conversation_id,
    )

    save_user_message_mock.assert_called_once()

    rag_mock.assert_called_once()

    save_assistant_message_mock.assert_called_once()

    db_mock.commit.assert_called_once()


def test_chat_returns_404_when_project_does_not_exist(
    client: TestClient,
    db_mock: MagicMock,
) -> None:
    project_id = uuid4()

    db_mock.get.return_value = None

    response = client.post(
        "/chat",
        json={
            "project_id": str(
                project_id,
            ),
            "message": "Hola",
            "top_k": 5,
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Proyecto no encontrado",
    }


def test_chat_returns_409_when_project_is_not_indexed(
    client: TestClient,
    db_mock: MagicMock,
    current_user,
) -> None:
    project_id = uuid4()

    project = SimpleNamespace(
        id=project_id,
        owner_id=current_user.id,
        status="CHUNKED",
    )

    db_mock.get.return_value = project

    response = client.post(
        "/chat",
        json={
            "project_id": str(
                project_id,
            ),
            "message": "Hola",
            "top_k": 5,
        },
    )

    assert response.status_code == 409


def test_chat_returns_404_when_conversation_does_not_exist(
    client: TestClient,
    db_mock: MagicMock,
    current_user,
) -> None:
    project_id = uuid4()
    conversation_id = uuid4()

    project = SimpleNamespace(
        id=project_id,
        owner_id=current_user.id,
        status="INDEXED",
    )

    db_mock.get.return_value = project

    with patch(
        "app.routers.chat."
        "get_conversation_for_project",
        side_effect=HTTPException(
            status_code=404,
            detail=(
                "Conversación no encontrada"
            ),
        ),
    ):
        response = client.post(
            "/chat",
            json={
                "project_id": str(
                    project_id,
                ),
                "conversation_id": str(
                    conversation_id,
                ),
                "message": "Continúa.",
                "top_k": 5,
            },
        )

    assert response.status_code == 404

    assert response.json() == {
        "detail": (
            "Conversación no encontrada"
        ),
    }


def test_chat_returns_409_when_conversation_belongs_to_another_project(
    client: TestClient,
    db_mock: MagicMock,
    current_user,
) -> None:
    project_id = uuid4()
    conversation_id = uuid4()

    project = SimpleNamespace(
        id=project_id,
        owner_id=current_user.id,
        status="INDEXED",
    )

    db_mock.get.return_value = project

    with patch(
        "app.routers.chat."
        "get_conversation_for_project",
        side_effect=HTTPException(
            status_code=409,
            detail=(
                "La conversación no pertenece "
                "al proyecto indicado."
            ),
        ),
    ):
        response = client.post(
            "/chat",
            json={
                "project_id": str(
                    project_id,
                ),
                "conversation_id": str(
                    conversation_id,
                ),
                "message": "Continúa.",
                "top_k": 5,
            },
        )

    assert response.status_code == 409

    assert response.json() == {
        "detail": (
            "La conversación no pertenece "
            "al proyecto indicado."
        ),
    }


def test_chat_rolls_back_when_embedding_configuration_fails(
    client: TestClient,
    db_mock: MagicMock,
    current_user,
) -> None:
    project_id = uuid4()
    conversation_id = uuid4()

    project = SimpleNamespace(
        id=project_id,
        owner_id=current_user.id,
        status="INDEXED",
    )

    conversation = SimpleNamespace(
        id=conversation_id,
        project_id=project_id,
    )

    db_mock.get.return_value = project

    with (
        patch(
            "app.routers.chat."
            "create_conversation",
            return_value=conversation,
        ),
        patch(
            "app.routers.chat."
            "save_user_message",
        ),
        patch(
            "app.routers.chat."
            "answer_project_question",
            side_effect=(
                EmbeddingConfigurationError(
                    "OPENAI_API_KEY="
                    "internal-secret"
                )
            ),
        ),
    ):
        response = client.post(
            "/chat",
            json={
                "project_id": str(
                    project_id,
                ),
                "message": "Hola",
                "top_k": 5,
            },
        )

    assert response.status_code == 500

    assert (
        "internal-secret"
        not in response.text
    )

    assert (
        "OPENAI_API_KEY"
        not in response.text
    )

    db_mock.rollback.assert_called_once()

    db_mock.commit.assert_not_called()


def test_chat_returns_404_for_other_users_project(
    client: TestClient,
    db_mock: MagicMock,
    current_user,
) -> None:
    project_id = uuid4()

    project = SimpleNamespace(
        id=project_id,
        owner_id=uuid4(),
        status="INDEXED",
    )

    db_mock.get.return_value = project

    with patch(
        "app.routers.chat."
        "answer_project_question",
    ) as rag_mock:
        response = client.post(
            "/chat",
            json={
                "project_id": str(
                    project_id,
                ),
                "message": (
                    "Analiza este proyecto."
                ),
                "top_k": 5,
            },
        )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Proyecto no encontrado",
    }

    rag_mock.assert_not_called()


def test_chat_does_not_reveal_status_of_other_users_project(
    client: TestClient,
    db_mock: MagicMock,
    current_user,
) -> None:
    project_id = uuid4()

    project = SimpleNamespace(
        id=project_id,
        owner_id=uuid4(),
        status="CREATED",
    )

    db_mock.get.return_value = project

    with patch(
        "app.routers.chat."
        "answer_project_question",
    ) as rag_mock:
        response = client.post(
            "/chat",
            json={
                "project_id": str(
                    project_id,
                ),
                "message": (
                    "Analiza este proyecto."
                ),
                "top_k": 5,
            },
        )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Proyecto no encontrado",
    }

    assert (
        "INDEXED"
        not in response.text
    )

    assert (
        "indexado"
        not in response.text.lower()
    )

    rag_mock.assert_not_called()