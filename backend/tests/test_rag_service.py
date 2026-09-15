from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.services.rag_service import (
    MAX_EXCERPT_LENGTH,
    MAX_HISTORY_MESSAGES,
    RagHistoryMessage,
    _build_conversation_history,
    _create_excerpt,
    answer_project_question,
)
from app.services.semantic_search_service import (
    SemanticSearchResult,
)


def create_search_result(
    *,
    path: str = "src/app/app.ts",
    language: str = "typescript",
    chunk_index: int = 0,
    content: str = "export const hello = 'DevPilot AI';",
    distance: float = 0.1,
) -> SemanticSearchResult:
    return SemanticSearchResult(
        chunk_id=uuid4(),
        document_id=uuid4(),
        path=path,
        language=language,
        chunk_index=chunk_index,
        content=content,
        distance=distance,
    )


def test_empty_history_returns_default_message() -> None:
    result = _build_conversation_history(
        [],
    )

    assert result == (
        "No hay mensajes anteriores."
    )


def test_conversation_history_contains_roles() -> None:
    history = [
        RagHistoryMessage(
            role="user",
            content="¿Qué hace este archivo?",
        ),
        RagHistoryMessage(
            role="assistant",
            content="Exporta una constante.",
        ),
    ]

    result = _build_conversation_history(
        history,
    )

    assert (
        "Usuario: ¿Qué hace este archivo?"
        in result
    )

    assert (
        "DevPilot: Exporta una constante."
        in result
    )


def test_conversation_history_uses_only_recent_messages() -> None:
    history = [
        RagHistoryMessage(
            role="user",
            content=f"mensaje-{index}",
        )
        for index in range(
            MAX_HISTORY_MESSAGES + 5,
        )
    ]

    result = _build_conversation_history(
        history,
    )

    assert "mensaje-0" not in result
    assert "mensaje-4" not in result

    assert "mensaje-5" in result

    assert (
        f"mensaje-{MAX_HISTORY_MESSAGES + 4}"
        in result
    )


def test_excerpt_returns_short_content_unchanged() -> None:
    content = (
        "export const hello = 'DevPilot AI';"
    )

    result = _create_excerpt(
        content,
    )

    assert result == content


def test_excerpt_truncates_long_content() -> None:
    content = "A" * (
        MAX_EXCERPT_LENGTH + 100
    )

    result = _create_excerpt(
        content,
    )

    assert result.endswith(
        "...",
    )

    assert len(result) == (
        MAX_EXCERPT_LENGTH + 3
    )


@patch(
    "app.services.rag_service."
    "_create_openai_client",
)
@patch(
    "app.services.rag_service."
    "search_project_chunks",
)
def test_rag_returns_insufficient_context_when_no_results(
    mock_search: MagicMock,
    mock_create_client: MagicMock,
) -> None:
    mock_search.return_value = []

    db = MagicMock()
    project_id = uuid4()

    result = answer_project_question(
        db=db,
        project_id=project_id,
        question="¿Qué hace este proyecto?",
        top_k=5,
    )

    assert (
        "No he encontrado suficiente contexto"
        in result.answer
    )

    assert result.sources == []

    mock_search.assert_called_once_with(
        db=db,
        project_id=project_id,
        query="¿Qué hace este proyecto?",
        top_k=5,
    )

    mock_create_client.assert_not_called()


@patch(
    "app.services.rag_service."
    "_create_openai_client",
)
@patch(
    "app.services.rag_service."
    "search_project_chunks",
)
def test_rag_calls_llm_with_retrieved_context(
    mock_search: MagicMock,
    mock_create_client: MagicMock,
) -> None:
    search_result = create_search_result()

    mock_search.return_value = [
        search_result,
    ]

    mock_client = MagicMock()

    mock_client.responses.create.return_value = (
        SimpleNamespace(
            output_text=(
                "El archivo exporta una constante "
                "llamada `hello`."
            ),
        )
    )

    mock_create_client.return_value = (
        mock_client
    )

    db = MagicMock()
    project_id = uuid4()

    result = answer_project_question(
        db=db,
        project_id=project_id,
        question=(
            "¿Qué exporta este archivo?"
        ),
        top_k=5,
    )

    assert result.answer == (
        "El archivo exporta una constante "
        "llamada `hello`."
    )

    assert len(result.sources) == 1

    assert (
        result.sources[0].path
        == "src/app/app.ts"
    )

    assert (
        result.sources[0].language
        == "typescript"
    )

    assert (
        result.sources[0].chunk_index
        == 0
    )

    mock_client.responses.create.assert_called_once()

    call_kwargs = (
        mock_client
        .responses
        .create
        .call_args
        .kwargs
    )

    assert (
        "¿Qué exporta este archivo?"
        in call_kwargs["input"]
    )

    assert (
        "src/app/app.ts"
        in call_kwargs["input"]
    )

    assert (
        "export const hello = 'DevPilot AI';"
        in call_kwargs["input"]
    )


@patch(
    "app.services.rag_service."
    "_create_openai_client",
)
@patch(
    "app.services.rag_service."
    "search_project_chunks",
)
def test_rag_includes_conversation_history(
    mock_search: MagicMock,
    mock_create_client: MagicMock,
) -> None:
    mock_search.return_value = [
        create_search_result(),
    ]

    mock_client = MagicMock()

    mock_client.responses.create.return_value = (
        SimpleNamespace(
            output_text=(
                "El valor es `DevPilot AI`."
            ),
        )
    )

    mock_create_client.return_value = (
        mock_client
    )

    history = [
        RagHistoryMessage(
            role="user",
            content=(
                "¿Cómo se llama la constante?"
            ),
        ),
        RagHistoryMessage(
            role="assistant",
            content=(
                "La constante se llama hello."
            ),
        ),
    ]

    result = answer_project_question(
        db=MagicMock(),
        project_id=uuid4(),
        question="¿Y qué valor tiene?",
        history=history,
    )

    assert result.answer == (
        "El valor es `DevPilot AI`."
    )

    call_kwargs = (
        mock_client
        .responses
        .create
        .call_args
        .kwargs
    )

    prompt = call_kwargs[
        "input"
    ]

    assert (
        "Usuario: ¿Cómo se llama la constante?"
        in prompt
    )

    assert (
        "DevPilot: La constante se llama hello."
        in prompt
    )

    assert (
        "¿Y qué valor tiene?"
        in prompt
    )


@patch(
    "app.services.rag_service."
    "_create_openai_client",
)
@patch(
    "app.services.rag_service."
    "search_project_chunks",
)
def test_rag_generates_sources_from_search_results(
    mock_search: MagicMock,
    mock_create_client: MagicMock,
) -> None:
    mock_search.return_value = [
        create_search_result(
            path="src/app/app.ts",
            chunk_index=0,
        ),
        create_search_result(
            path="src/app/app.config.ts",
            chunk_index=1,
            content=(
                "export const appConfig = {};"
            ),
        ),
    ]

    mock_client = MagicMock()

    mock_client.responses.create.return_value = (
        SimpleNamespace(
            output_text="Respuesta.",
        )
    )

    mock_create_client.return_value = (
        mock_client
    )

    result = answer_project_question(
        db=MagicMock(),
        project_id=uuid4(),
        question=(
            "¿Cómo está configurada la aplicación?"
        ),
    )

    assert len(
        result.sources,
    ) == 2

    assert (
        result.sources[0].path
        == "src/app/app.ts"
    )

    assert (
        result.sources[1].path
        == "src/app/app.config.ts"
    )

    assert (
        result.sources[1].chunk_index
        == 1
    )


@patch(
    "app.services.rag_service."
    "_create_openai_client",
)
@patch(
    "app.services.rag_service."
    "search_project_chunks",
)
def test_rag_handles_empty_llm_response(
    mock_search: MagicMock,
    mock_create_client: MagicMock,
) -> None:
    mock_search.return_value = [
        create_search_result(),
    ]

    mock_client = MagicMock()

    mock_client.responses.create.return_value = (
        SimpleNamespace(
            output_text="   ",
        )
    )

    mock_create_client.return_value = (
        mock_client
    )

    result = answer_project_question(
        db=MagicMock(),
        project_id=uuid4(),
        question="¿Qué hace?",
    )

    assert result.answer == (
        "No se pudo generar una respuesta "
        "a partir del contexto recuperado."
    )
    
@patch(
    "app.services.rag_service."
    "_create_openai_client",
)
@patch(
    "app.services.rag_service."
    "search_project_chunks",
)
def test_rag_redacts_secrets_from_answer_and_sources(
    mock_search: MagicMock,
    mock_create_client: MagicMock,
) -> None:
    secret = (
        "sk-proj-"
        "abcdefghijklmnopqrstuvwxyz123456"
    )

    mock_search.return_value = [
        create_search_result(
            content=(
                f"const key = '{secret}';"
            ),
        ),
    ]

    mock_client = MagicMock()

    mock_client.responses.create.return_value = (
        SimpleNamespace(
            output_text=(
                f"La clave encontrada es {secret}"
            ),
        )
    )

    mock_create_client.return_value = (
        mock_client
    )

    result = answer_project_question(
        db=MagicMock(),
        project_id=uuid4(),
        question="Analiza config.",
    )

    assert secret not in result.answer

    assert (
        "[REDACTED_SECRET]"
        in result.answer
    )

    assert len(
        result.sources,
    ) == 1

    assert (
        secret
        not in result.sources[0].excerpt
    )

    assert (
        "[REDACTED_SECRET]"
        in result.sources[0].excerpt
    )