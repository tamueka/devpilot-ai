from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.db.database import get_db
from app.main import app
from app.security.upload_size import (
    UploadTooLargeError,
)
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


def test_upload_returns_413_when_archive_is_too_large(
    client: TestClient,
    db_mock: MagicMock,
    current_user,
) -> None:
    project_id = uuid4()

    db_mock.get.return_value = (
        SimpleNamespace(
            id=project_id,
            owner_id=current_user.id,
            status="CREATED",
            uploaded_file=None,
        )
    )

    with patch(
        "app.routers.projects."
        "save_stream_with_size_limit",
        side_effect=UploadTooLargeError(
            "Archivo demasiado grande.",
        ),
    ):
        response = client.post(
            f"/projects/{project_id}/upload",
            files={
                "file": (
                    "project.zip",
                    b"fake zip",
                    "application/zip",
                ),
            },
        )

    assert response.status_code == 413

    assert response.json() == {
        "detail": (
        "El archivo comprimido supera "
        "el tamaño máximo permitido "
        "de 50 MB."
     ),
    }