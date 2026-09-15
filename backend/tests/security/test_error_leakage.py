from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from app.db.database import get_db
from app.main import app
from app.services.project_embedding_service import (
    EmbeddingConfigurationError,
)
from app.security.current_user import (
    get_current_user,
)


SECRET_MARKER = (
    "SUPER_SECRET_OPENAI_KEY_123456789"
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
    app.dependency_overrides[
        get_db
    ] = lambda: db_mock

    app.dependency_overrides[
        get_current_user
    ] = lambda: current_user

    try:
        yield TestClient(
            app,
        )
    finally:
        app.dependency_overrides.pop(
            get_db,
            None,
        )
        app.dependency_overrides.pop(
            get_current_user,
            None,
        )


def test_chat_does_not_expose_internal_ai_error(
    client: TestClient,
    db_mock: MagicMock,
    current_user,
) -> None:
    project_id = uuid4()

    db_mock.get.return_value = (
        SimpleNamespace(
            id=project_id,
            owner_id=current_user.id,
            status="INDEXED",
        )
    )

    internal_error = (
        "OPENAI_API_KEY="
        + SECRET_MARKER
    )

    with (
        patch(
            "app.routers.chat."
            "create_conversation",
            return_value=SimpleNamespace(
                id=uuid4(),
                project_id=project_id,
            ),
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
                    internal_error,
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
                "message": "Analiza el proyecto.",
                "top_k": 5,
            },
        )

    assert response.status_code == 500

    body = response.text

    assert SECRET_MARKER not in body

    assert (
        "OPENAI_API_KEY"
        not in body
    )

    assert response.json() == {
        "detail": (
            "El servicio de IA "
            "no está disponible."
        ),
    }

    db_mock.rollback.assert_called_once()


def test_readme_does_not_expose_internal_ai_error(
    client: TestClient,
    db_mock: MagicMock,
    current_user,
) -> None:
    project_id = uuid4()

    db_mock.get.return_value = (
        SimpleNamespace(
            id=project_id,
            owner_id=current_user.id,
            status="INDEXED",
        )
    )

    internal_error = (
        "Provider error. Token: "
        + SECRET_MARKER
    )

    with patch(
        "app.routers.readme."
        "generate_project_readme",
        side_effect=(
            EmbeddingConfigurationError(
                internal_error,
            )
        ),
    ):
        response = client.post(
            f"/projects/{project_id}/readme",
            json={
                "project_id": str(
                    project_id,
                ),
                "language": "es",
            },
        )

    assert response.status_code == 500

    assert (
        SECRET_MARKER
        not in response.text
    )

    assert response.json() == {
        "detail": (
            "El servicio de IA "
            "no está disponible."
        ),
    }


def test_unit_test_generation_does_not_expose_internal_error(
    client: TestClient,
    db_mock: MagicMock,
    current_user,
) -> None:
    project_id = uuid4()
    document_id = uuid4()

    project = SimpleNamespace(
        id=project_id,
        owner_id=current_user.id,
        status="INDEXED",
    )

    document = SimpleNamespace(
        id=document_id,
        project_id=project_id,
    )

    db_mock.get.return_value = project

    internal_error = (
        "Local path: "
        "C:\\Users\\private\\"
        + SECRET_MARKER
    )

    with (
        patch(
            "app.routers.projects."
            "get_document_for_project",
            return_value=document,
        ),
        patch(
            "app.routers.projects."
            "generate_document_unit_tests",
            side_effect=RuntimeError(
                internal_error,
            ),
        ),
    ):
        response = client.post(
            f"/projects/{project_id}/unit-tests",
            json={
                "project_id": str(
                    project_id,
                ),
                "document_id": str(
                    document_id,
                ),
                "framework": None,
            },
        )

    assert response.status_code == 500

    assert response.json() == {
        "detail": (
            "No se pudieron generar "
            "los tests unitarios."
        ),
    }

    assert (
        SECRET_MARKER
        not in response.text
    )

    assert (
        internal_error
        not in response.text
    )


def test_fastapi_debug_mode_is_disabled() -> None:
    assert app.debug is False