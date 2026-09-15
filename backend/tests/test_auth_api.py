from datetime import (
    UTC,
    datetime,
)
from types import SimpleNamespace
from unittest.mock import (
    MagicMock,
    patch,
)
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.db.database import get_db
from app.routers.auth import router
from app.security.current_user import (
    get_current_user,
)


@pytest.fixture
def db_mock() -> MagicMock:
    return MagicMock()


@pytest.fixture
def client(
    db_mock: MagicMock,
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

    return TestClient(
        app,
    )


def test_register_creates_user(
    client: TestClient,
    db_mock: MagicMock,
) -> None:
    user_id = uuid4()

    user = SimpleNamespace(
        id=user_id,
        email="user@example.com",
        is_active=True,
        created_at=datetime.now(
            UTC,
        ),
    )

    with (
        patch(
            "app.routers.auth."
            "get_user_by_email",
            return_value=None,
        ),
        patch(
            "app.routers.auth."
            "create_user",
            return_value=user,
        ) as create_mock,
    ):
        response = client.post(
            "/auth/register",
            json={
                "email": "USER@example.com",
                "password": (
                    "SecurePassword123!"
                ),
            },
        )

    assert response.status_code == 201

    assert (
        response.json()["id"]
        == str(user_id)
    )

    assert (
        response.json()["email"]
        == "user@example.com"
    )

    create_mock.assert_called_once()

    db_mock.commit.assert_called_once()


def test_register_rejects_duplicate_email(
    client: TestClient,
) -> None:
    with patch(
        "app.routers.auth."
        "get_user_by_email",
        return_value=SimpleNamespace(),
    ):
        response = client.post(
            "/auth/register",
            json={
                "email": "user@example.com",
                "password": (
                    "SecurePassword123!"
                ),
            },
        )

    assert response.status_code == 409


def test_register_rejects_invalid_email(
    client: TestClient,
) -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": "invalid-email",
            "password": (
                "SecurePassword123!"
            ),
        },
    )

    assert response.status_code == 422


def test_register_rejects_short_password(
    client: TestClient,
) -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "short",
        },
    )

    assert response.status_code == 422


def test_login_returns_access_token(
    client: TestClient,
) -> None:
    user_id = uuid4()

    user = SimpleNamespace(
        id=user_id,
        email="user@example.com",
        is_active=True,
    )

    with (
        patch(
            "app.routers.auth."
            "authenticate_user",
            return_value=user,
        ),
        patch(
            "app.routers.auth."
            "create_access_token",
            return_value="signed-jwt",
        ) as token_mock,
    ):
        response = client.post(
            "/auth/login",
            json={
                "email": "user@example.com",
                "password": (
                    "SecurePassword123!"
                ),
            },
        )

    assert response.status_code == 200

    assert response.json() == {
        "access_token": "signed-jwt",
        "token_type": "bearer",
    }

    token_mock.assert_called_once_with(
        user_id,
    )


def test_login_rejects_invalid_credentials(
    client: TestClient,
) -> None:
    with patch(
        "app.routers.auth."
        "authenticate_user",
        return_value=None,
    ):
        response = client.post(
            "/auth/login",
            json={
                "email": "user@example.com",
                "password": "wrong-password",
            },
        )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Credenciales inválidas.",
    }


def test_me_returns_current_user(
    db_mock: MagicMock,
) -> None:
    user_id = uuid4()

    user = SimpleNamespace(
        id=user_id,
        email="user@example.com",
        is_active=True,
        created_at=datetime.now(
            UTC,
        ),
    )

    app = FastAPI()

    app.include_router(
        router,
    )

    app.dependency_overrides[
        get_current_user
    ] = lambda: user

    client = TestClient(
        app,
    )

    response = client.get(
        "/auth/me",
    )

    assert response.status_code == 200

    assert (
        response.json()["id"]
        == str(user_id)
    )

    assert (
        response.json()["email"]
        == "user@example.com"
    )