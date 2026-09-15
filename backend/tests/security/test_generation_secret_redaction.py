from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.services.readme_service import (
    generate_project_readme,
)
from app.services.semantic_search_service import (
    SemanticSearchResult,
)
from app.services.unit_test_service import (
    generate_document_unit_tests,
)


SECRET = (
    "sk-proj-"
    "abcdefghijklmnopqrstuvwxyz123456"
)

REDACTED = "[REDACTED_SECRET]"


def create_search_result(
    content: str,
    *,
    path: str = "src/config.ts",
) -> SemanticSearchResult:
    return SemanticSearchResult(
        chunk_id=uuid4(),
        document_id=uuid4(),
        path=path,
        language="typescript",
        chunk_index=0,
        content=content,
        distance=0.01,
    )


def create_mock_client(
    output_text: str,
) -> MagicMock:
    client = MagicMock()

    client.responses.create.return_value = (
        SimpleNamespace(
            output_text=output_text,
        )
    )

    return client


# =========================================================
# README
# =========================================================


@patch(
    "app.services.readme_service."
    "_create_openai_client",
)
@patch(
    "app.services.readme_service."
    "search_project_chunks",
)
def test_readme_redacts_secret_before_sending_context_to_llm(
    mock_search: MagicMock,
    mock_create_client: MagicMock,
) -> None:
    mock_search.return_value = [
        create_search_result(
            content=(
                "export const apiKey = "
                f"'{SECRET}';"
            ),
        ),
    ]

    client = create_mock_client(
        "# README\n\nContenido seguro.",
    )

    mock_create_client.return_value = client

    generate_project_readme(
        db=MagicMock(),
        project_id=uuid4(),
        language="es",
    )

    client.responses.create.assert_called_once()

    request = (
        client
        .responses
        .create
        .call_args
        .kwargs
    )

    assert SECRET not in str(
        request,
    )

    assert REDACTED in request["input"]


@patch(
    "app.services.readme_service."
    "_create_openai_client",
)
@patch(
    "app.services.readme_service."
    "search_project_chunks",
)
def test_readme_redacts_secret_from_llm_response(
    mock_search: MagicMock,
    mock_create_client: MagicMock,
) -> None:
    mock_search.return_value = [
        create_search_result(
            content=(
                "export const app = true;"
            ),
        ),
    ]

    client = create_mock_client(
        (
            "# Configuración\n\n"
            f"La clave es {SECRET}"
        ),
    )

    mock_create_client.return_value = client

    result = generate_project_readme(
        db=MagicMock(),
        project_id=uuid4(),
        language="es",
    )

    assert SECRET not in result.content

    assert REDACTED in result.content


# =========================================================
# UNIT TEST GENERATION
# =========================================================


@patch(
    "app.services.unit_test_service."
    "_create_openai_client",
)
@patch(
    "app.services.unit_test_service."
    "_get_related_context",
)
@patch(
    "app.services.unit_test_service."
    "_get_project_context_documents",
)
def test_unit_test_generation_redacts_secret_before_llm(
    mock_project_context: MagicMock,
    mock_related_context: MagicMock,
    mock_create_client: MagicMock,
) -> None:
    project_id = uuid4()
    document_id = uuid4()

    selected_document = SimpleNamespace(
        id=document_id,
        project_id=project_id,
        path="src/app.ts",
        filename="app.ts",
        extension=".ts",
        language="typescript",
        content=(
            "export const apiKey = "
            f"'{SECRET}';"
        ),
    )

    config_document = SimpleNamespace(
        id=uuid4(),
        project_id=project_id,
        path="package.json",
        filename="package.json",
        extension=".json",
        language="json",
        content=(
            '{"apiKey": "'
            + SECRET
            + '"}'
        ),
    )

    db = MagicMock()

    db.get.return_value = (
        selected_document
    )

    mock_project_context.return_value = [
        config_document,
    ]

    mock_related_context.return_value = [
        create_search_result(
            content=(
                "const token = "
                f"'{SECRET}';"
            ),
        ),
    ]

    client = create_mock_client(
        (
            "describe('App', () => {\n"
            "  it('works', () => {});\n"
            "});"
        ),
    )

    mock_create_client.return_value = client

    generate_document_unit_tests(
        db=db,
        project_id=project_id,
        document_id=document_id,
        framework="Vitest",
    )

    client.responses.create.assert_called_once()

    request = (
        client
        .responses
        .create
        .call_args
        .kwargs
    )

    assert SECRET not in str(
        request,
    )

    assert REDACTED in request["input"]


@patch(
    "app.services.unit_test_service."
    "_create_openai_client",
)
@patch(
    "app.services.unit_test_service."
    "_get_related_context",
)
@patch(
    "app.services.unit_test_service."
    "_get_project_context_documents",
)
def test_unit_test_generation_redacts_secret_from_llm_response(
    mock_project_context: MagicMock,
    mock_related_context: MagicMock,
    mock_create_client: MagicMock,
) -> None:
    project_id = uuid4()
    document_id = uuid4()

    selected_document = SimpleNamespace(
        id=document_id,
        project_id=project_id,
        path="src/app.ts",
        filename="app.ts",
        extension=".ts",
        language="typescript",
        content=(
            "export const app = true;"
        ),
    )

    db = MagicMock()

    db.get.return_value = (
        selected_document
    )

    mock_project_context.return_value = []
    mock_related_context.return_value = []

    client = create_mock_client(
        (
            "const apiKey = "
            f"'{SECRET}';\n"
            "\n"
            "describe('App', () => {});"
        ),
    )

    mock_create_client.return_value = client

    result = generate_document_unit_tests(
        db=db,
        project_id=project_id,
        document_id=document_id,
        framework="Vitest",
    )

    assert SECRET not in result.content

    assert REDACTED in result.content