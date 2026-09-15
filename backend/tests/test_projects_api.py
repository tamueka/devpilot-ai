from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.db.database import get_db
from app.main import app
from app.security.current_user import (
    get_current_user,
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

    yield TestClient(
        app,
    )
    app.dependency_overrides.pop(
        get_db,
        None,
    )
    app.dependency_overrides.pop(
        get_current_user,
        None,
    )


def test_list_project_documents_returns_documents(
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
        path="src/app/app.ts",
        filename="app.ts",
        extension=".ts",
        language="typescript",
        size=120,
    )

    db_mock.get.return_value = project

    with patch(
        "app.routers.projects."
        "get_project_documents",
        return_value=[document],
    ) as get_documents_mock:
        response = client.get(
            f"/projects/{project_id}/documents",
        )

    assert response.status_code == 200

    assert response.json() == [
        {
            "id": str(document_id),
            "project_id": str(project_id),
            "path": "src/app/app.ts",
            "filename": "app.ts",
            "extension": ".ts",
            "language": "typescript",
            "size": 120,
        }
    ]

    db_mock.get.assert_called_once()

    get_documents_mock.assert_called_once_with(
        db=db_mock,
        project_id=project_id,
    )


def test_list_project_documents_returns_404_when_project_does_not_exist(
    client: TestClient,
    db_mock: MagicMock,
) -> None:
    project_id = uuid4()

    db_mock.get.return_value = None

    response = client.get(
        f"/projects/{project_id}/documents",
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Proyecto no encontrado",
    }


def test_list_project_documents_returns_409_when_project_is_not_indexed(
    client: TestClient,
    db_mock: MagicMock,
    current_user,
) -> None:
    project_id = uuid4()

    project = SimpleNamespace(
        id=project_id,
        owner_id=current_user.id,
        status="CREATED",
    )

    db_mock.get.return_value = project

    response = client.get(
        f"/projects/{project_id}/documents",
    )

    assert response.status_code == 409