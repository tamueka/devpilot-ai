from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.db.database import get_db
from app.routers.projects import router as projects_router
from app.routers.readme import router as readme_router
from app.security.rate_limiter import (
    enforce_generation_rate_limit,
)
from app.services.project_embedding_service import (
    EmbeddingConfigurationError,
)
from app.services.readme_service import (
    ReadmeResult,
    ReadmeSource,
)
from app.services.unit_test_service import (
    UnitTestResult,
    UnitTestSource,
)
from app.security.current_user import (
    get_current_user,
)


@pytest.fixture
def db_mock() -> MagicMock:
    return MagicMock()


@pytest.fixture
def client(
    db_mock: MagicMock,
    current_user,
) -> TestClient:
    app = FastAPI()

    app.include_router(
        projects_router,
    )

    app.include_router(
        readme_router,
    )

    def override_get_db():
        yield db_mock

    app.dependency_overrides[
        get_db
    ] = override_get_db

    app.dependency_overrides[
        get_current_user
    ] = lambda: current_user

    app.dependency_overrides[
        enforce_generation_rate_limit
    ] = lambda: None

    return TestClient(
        app,
    )
    
@pytest.fixture
def current_user():
    return SimpleNamespace(
        id=uuid4(),
        email="test@example.com",
        is_active=True,
    )


# =========================================================
# README
# =========================================================


def test_generate_readme_returns_generated_content(
    client: TestClient,
    db_mock: MagicMock,
    current_user,
) -> None:
    project_id = uuid4()

    project = SimpleNamespace(
        id=project_id,
        owner_id=current_user.id,
        status="INDEXED",
    )

    db_mock.get.return_value = project

    readme_result = ReadmeResult(
        content=(
            "# DevPilot AI\n\n"
            "Proyecto de ejemplo."
        ),
        sources=[
            ReadmeSource(
                path="src/app/app.ts",
                language="typescript",
            ),
        ],
    )

    with patch(
        "app.routers.readme."
        "generate_project_readme",
        return_value=readme_result,
    ) as generate_mock:
        response = client.post(
            f"/projects/{project_id}/readme",
            json={
                "project_id": str(
                    project_id,
                ),
                "language": "es",
            },
        )

    assert response.status_code == 200

    assert response.json() == {
        "content": (
            "# DevPilot AI\n\n"
            "Proyecto de ejemplo."
        ),
        "sources": [
            {
                "path": "src/app/app.ts",
                "language": "typescript",
            },
        ],
    }

    generate_mock.assert_called_once_with(
        db=db_mock,
        project_id=project_id,
        language="es",
    )


def test_generate_readme_returns_404_when_project_does_not_exist(
    client: TestClient,
    db_mock: MagicMock,
) -> None:
    project_id = uuid4()

    db_mock.get.return_value = None

    response = client.post(
        f"/projects/{project_id}/readme",
        json={
            "project_id": str(
                project_id,
            ),
            "language": "es",
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Proyecto no encontrado",
    }


def test_generate_readme_returns_400_when_project_ids_do_not_match(
    client: TestClient,
    db_mock: MagicMock,
    current_user,
) -> None:
    project_id = uuid4()
    other_project_id = uuid4()

    db_mock.get.return_value = (
        SimpleNamespace(
            id=project_id,
            owner_id=current_user.id,
            status="INDEXED",
        )
    )

    response = client.post(
        f"/projects/{project_id}/readme",
        json={
            "project_id": str(
                other_project_id,
            ),
            "language": "es",
        },
    )

    assert response.status_code == 400


def test_generate_readme_returns_409_when_project_is_not_indexed(
    client: TestClient,
    db_mock: MagicMock,
    current_user,
) -> None:
    project_id = uuid4()

    db_mock.get.return_value = (
        SimpleNamespace(
            id=project_id,
            owner_id=current_user.id,
            status="CHUNKED",
        )
    )

    response = client.post(
        f"/projects/{project_id}/readme",
        json={
            "project_id": str(
                project_id,
            ),
            "language": "es",
        },
    )

    assert response.status_code == 409


def test_generate_readme_returns_422_when_context_is_insufficient(
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

    with patch(
        "app.routers.readme."
        "generate_project_readme",
        side_effect=ValueError(
            (
                "No hay suficiente código "
                "indexado para generar el README."
            ),
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

    assert response.status_code == 422

    assert response.json() == {
        "detail": (
            "No hay suficiente código "
            "indexado para generar el README."
        ),
    }


def test_generate_readme_returns_500_when_ai_is_not_configured(
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

    with patch(
        "app.routers.readme."
        "generate_project_readme",
        side_effect=(
            EmbeddingConfigurationError(
                "OPENAI_API_KEY=internal-secret",
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

    assert response.json() == {
        "detail": (
            "El servicio de IA "
            "no está disponible."
        ),
    }

    assert (
        "internal-secret"
        not in response.text
    )


# =========================================================
# UNIT TESTS
# =========================================================


def test_generate_unit_tests_returns_generated_code(
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

    unit_test_result = UnitTestResult(
        content=(
            "describe('hello', () => {\n"
            "  it('should expose the value', () => {\n"
            "    expect(hello).toBe('DevPilot AI');\n"
            "  });\n"
            "});"
        ),
        suggested_filename="index.spec.ts",
        sources=[
            UnitTestSource(
                path="test-project/index.ts",
                language="typescript",
            ),
        ],
    )

    with (
        patch(
            "app.routers.projects."
            "get_document_for_project",
            return_value=document,
        ) as document_guard_mock,
        patch(
            "app.routers.projects."
            "generate_document_unit_tests",
            return_value=unit_test_result,
        ) as generate_mock,
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

    assert response.status_code == 200

    assert response.json() == {
        "content": (
            "describe('hello', () => {\n"
            "  it('should expose the value', () => {\n"
            "    expect(hello).toBe('DevPilot AI');\n"
            "  });\n"
            "});"
        ),
        "suggested_filename": (
            "index.spec.ts"
        ),
        "sources": [
            {
                "path": (
                    "test-project/index.ts"
                ),
                "language": (
                    "typescript"
                ),
            },
        ],
    }

    document_guard_mock.assert_called_once_with(
        db=db_mock,
        document_id=document_id,
        project_id=project_id,
    )

    generate_mock.assert_called_once_with(
        db=db_mock,
        project_id=project_id,
        document_id=document_id,
        framework=None,
    )


def test_generate_unit_tests_passes_selected_framework(
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

    result = UnitTestResult(
        content=(
            "test('example', () => {});"
        ),
        suggested_filename=(
            "app.spec.ts"
        ),
        sources=[],
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
            return_value=result,
        ) as generate_mock,
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
                "framework": "Vitest",
            },
        )

    assert response.status_code == 200

    generate_mock.assert_called_once_with(
        db=db_mock,
        project_id=project_id,
        document_id=document_id,
        framework="Vitest",
    )


def test_generate_unit_tests_returns_404_when_project_does_not_exist(
    client: TestClient,
    db_mock: MagicMock,
) -> None:
    project_id = uuid4()
    document_id = uuid4()

    db_mock.get.return_value = None

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

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Proyecto no encontrado",
    }


def test_generate_unit_tests_returns_400_when_project_ids_do_not_match(
    client: TestClient,
    db_mock: MagicMock,
    current_user,
) -> None:
    project_id = uuid4()
    other_project_id = uuid4()
    document_id = uuid4()

    db_mock.get.return_value = (
        SimpleNamespace(
            id=project_id,
            owner_id=current_user.id,
            status="INDEXED",
        )
    )

    response = client.post(
        f"/projects/{project_id}/unit-tests",
        json={
            "project_id": str(
                other_project_id,
            ),
            "document_id": str(
                document_id,
            ),
            "framework": None,
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": (
            "El project_id de la URL no coincide "
            "con el project_id de la petición."
        ),
    }


def test_generate_unit_tests_returns_409_when_project_is_not_indexed(
    client: TestClient,
    db_mock: MagicMock,
    current_user,
) -> None:
    project_id = uuid4()
    document_id = uuid4()

    db_mock.get.return_value = (
        SimpleNamespace(
            id=project_id,
            owner_id=current_user.id,
            status="CHUNKED",
        )
    )

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

    assert response.status_code == 409

    assert response.json() == {
        "detail": (
            "El proyecto debe estar completamente "
            "indexado para generar tests."
        ),
    }


def test_generate_unit_tests_returns_422_when_document_is_invalid(
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

    with (
        patch(
            "app.routers.projects."
            "get_document_for_project",
            return_value=document,
        ),
        patch(
            "app.routers.projects."
            "generate_document_unit_tests",
            side_effect=ValueError(
                "Archivo no encontrado.",
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

    assert response.status_code == 422

    assert response.json() == {
        "detail": (
            "Archivo no encontrado."
        ),
    }


def test_generate_unit_tests_returns_500_when_generation_fails(
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
                (
                    "No se pudieron generar "
                    "los tests unitarios."
                ),
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


def test_generate_unit_tests_returns_404_when_document_belongs_to_other_project(
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

    db_mock.get.return_value = project

    with (
        patch(
            "app.routers.projects."
            "get_document_for_project",
            side_effect=HTTPException(
                status_code=404,
                detail=(
                    "Archivo no encontrado"
                ),
            ),
        ) as document_guard_mock,
        patch(
            "app.routers.projects."
            "generate_document_unit_tests",
        ) as generate_mock,
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

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Archivo no encontrado",
    }

    document_guard_mock.assert_called_once_with(
        db=db_mock,
        document_id=document_id,
        project_id=project_id,
    )

    generate_mock.assert_not_called()
    
def test_generate_readme_returns_404_for_other_users_project(
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
        "app.routers.readme.generate_project_readme",
    ) as generate_mock:
        response = client.post(
            f"/projects/{project_id}/readme",
            json={
                "project_id": str(
                    project_id,
                ),
                "language": "es",
            },
        )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Proyecto no encontrado",
    }

    generate_mock.assert_not_called()


def test_generate_readme_does_not_reveal_status_of_other_users_project(
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
        "app.routers.readme.generate_project_readme",
    ) as generate_mock:
        response = client.post(
            f"/projects/{project_id}/readme",
            json={
                "project_id": str(
                    project_id,
                ),
                "language": "es",
            },
        )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Proyecto no encontrado",
    }

    assert (
        "indexado"
        not in response.text.lower()
    )

    generate_mock.assert_not_called()