from datetime import (
    UTC,
    datetime,
)
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.db.database import get_db
from app.routers.projects import router
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
        email="owner@example.com",
        is_active=True,
    )


@pytest.fixture
def client(
    db_mock: MagicMock,
    current_user,
) -> TestClient:
    app = FastAPI()

    app.include_router(
        router,
    )

    def override_get_db():
        yield db_mock

    app.dependency_overrides[
        get_db
    ] = override_get_db

    app.dependency_overrides[
        get_current_user
    ] = lambda: current_user

    return TestClient(
        app,
    )


def test_create_project_assigns_current_user_as_owner(
    client: TestClient,
    db_mock: MagicMock,
    current_user,
) -> None:
    def refresh_project(project) -> None:
        project.id = uuid4()
        project.created_at = datetime.now(
            UTC,
        )
        project.updated_at = datetime.now(
            UTC,
        )

    db_mock.refresh.side_effect = (
        refresh_project
    )

    response = client.post(
        "/projects",
        json={
            "name": "DevPilot",
            "description": "TFM",
        },
    )

    assert response.status_code == 201

    project = (
        db_mock.add.call_args.args[0]
    )

    assert (
        project.owner_id
        == current_user.id
    )


def test_list_projects_filters_by_current_user(
    client: TestClient,
    db_mock: MagicMock,
    current_user,
) -> None:
    db_mock.execute.return_value.scalars.return_value.all.return_value = []

    response = client.get(
        "/projects",
    )

    assert response.status_code == 200

    statement = (
        db_mock.execute
        .call_args.args[0]
    )

    compiled = str(
        statement,
    )

    assert "owner_id" in compiled


def test_other_users_project_returns_404(
    client: TestClient,
    db_mock: MagicMock,
) -> None:
    project = SimpleNamespace(
        id=uuid4(),
        owner_id=uuid4(),
        status="INDEXED",
    )

    db_mock.get.return_value = project

    response = client.get(
        f"/projects/{project.id}",
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Proyecto no encontrado",
    }