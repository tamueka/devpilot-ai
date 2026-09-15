from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.security.resource_access import (
    get_conversation_for_project,
    get_conversation_or_404,
    get_document_for_project,
    get_indexed_project,
    get_project_or_404,
    get_indexed_project_for_user,
    get_project_for_user,
    get_conversation_for_user,
)


def test_returns_existing_project() -> None:
    project_id = uuid4()

    project = SimpleNamespace(
        id=project_id,
        status="INDEXED",
    )

    db = MagicMock()
    db.get.return_value = project

    result = get_project_or_404(
        db=db,
        project_id=project_id,
    )

    assert result is project


def test_missing_project_returns_404() -> None:
    db = MagicMock()
    db.get.return_value = None

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        get_project_or_404(
            db=db,
            project_id=uuid4(),
        )

    assert (
        exc_info.value.status_code
        == 404
    )

    assert (
        exc_info.value.detail
        == "Proyecto no encontrado"
    )


def test_indexed_project_is_allowed() -> None:
    project = SimpleNamespace(
        id=uuid4(),
        status="INDEXED",
    )

    db = MagicMock()
    db.get.return_value = project

    result = get_indexed_project(
        db=db,
        project_id=project.id,
    )

    assert result is project


def test_non_indexed_project_returns_409() -> None:
    project = SimpleNamespace(
        id=uuid4(),
        status="CHUNKED",
    )

    db = MagicMock()
    db.get.return_value = project

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        get_indexed_project(
            db=db,
            project_id=project.id,
        )

    assert (
        exc_info.value.status_code
        == 409
    )

    assert (
        exc_info.value.detail
        == (
            "El proyecto todavía no está "
            "completamente indexado."
        )
    )


def test_existing_conversation_is_returned() -> None:
    conversation_id = uuid4()

    conversation = SimpleNamespace(
        id=conversation_id,
        project_id=uuid4(),
    )

    db = MagicMock()
    db.get.return_value = conversation

    result = get_conversation_or_404(
        db=db,
        conversation_id=conversation_id,
    )

    assert result is conversation


def test_missing_conversation_or_404_returns_404() -> None:
    db = MagicMock()
    db.get.return_value = None

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        get_conversation_or_404(
            db=db,
            conversation_id=uuid4(),
        )

    assert (
        exc_info.value.status_code
        == 404
    )

    assert (
        exc_info.value.detail
        == "Conversación no encontrada"
    )


def test_conversation_from_same_project_is_allowed() -> None:
    project_id = uuid4()
    conversation_id = uuid4()

    conversation = SimpleNamespace(
        id=conversation_id,
        project_id=project_id,
    )

    db = MagicMock()
    db.get.return_value = conversation

    result = get_conversation_for_project(
        db=db,
        conversation_id=conversation_id,
        project_id=project_id,
    )

    assert result is conversation


def test_conversation_from_other_project_is_rejected() -> None:
    conversation_id = uuid4()
    project_id = uuid4()
    other_project_id = uuid4()

    conversation = SimpleNamespace(
        id=conversation_id,
        project_id=other_project_id,
    )

    db = MagicMock()
    db.get.return_value = conversation

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        get_conversation_for_project(
            db=db,
            conversation_id=conversation_id,
            project_id=project_id,
        )

    assert (
        exc_info.value.status_code
        == 409
    )

    assert (
        exc_info.value.detail
        == (
            "La conversación no pertenece "
            "al proyecto indicado."
        )
    )


def test_missing_conversation_returns_404() -> None:
    db = MagicMock()
    db.get.return_value = None

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        get_conversation_for_project(
            db=db,
            conversation_id=uuid4(),
            project_id=uuid4(),
        )

    assert (
        exc_info.value.status_code
        == 404
    )

    assert (
        exc_info.value.detail
        == "Conversación no encontrada"
    )


def test_document_from_same_project_is_allowed() -> None:
    project_id = uuid4()
    document_id = uuid4()

    document = SimpleNamespace(
        id=document_id,
        project_id=project_id,
    )

    db = MagicMock()
    db.get.return_value = document

    result = get_document_for_project(
        db=db,
        document_id=document_id,
        project_id=project_id,
    )

    assert result is document


def test_document_from_other_project_returns_404() -> None:
    project_id = uuid4()
    document_id = uuid4()
    other_project_id = uuid4()

    document = SimpleNamespace(
        id=document_id,
        project_id=other_project_id,
    )

    db = MagicMock()
    db.get.return_value = document

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        get_document_for_project(
            db=db,
            document_id=document_id,
            project_id=project_id,
        )

    assert (
        exc_info.value.status_code
        == 404
    )

    assert (
        exc_info.value.detail
        == "Archivo no encontrado"
    )


def test_missing_document_returns_404() -> None:
    db = MagicMock()
    db.get.return_value = None

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        get_document_for_project(
            db=db,
            document_id=uuid4(),
            project_id=uuid4(),
        )

    assert (
        exc_info.value.status_code
        == 404
    )

    assert (
        exc_info.value.detail
        == "Archivo no encontrado"
    )
def test_project_owner_can_access_project() -> None:
    user_id = uuid4()
    project_id = uuid4()

    project = SimpleNamespace(
        id=project_id,
        owner_id=user_id,
        status="INDEXED",
    )

    db = MagicMock()
    db.get.return_value = project

    result = get_project_for_user(
        db=db,
        project_id=project_id,
        user_id=user_id,
    )

    assert result is project


def test_other_user_cannot_access_project() -> None:
    owner_id = uuid4()
    attacker_id = uuid4()
    project_id = uuid4()

    project = SimpleNamespace(
        id=project_id,
        owner_id=owner_id,
        status="INDEXED",
    )

    db = MagicMock()
    db.get.return_value = project

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        get_project_for_user(
            db=db,
            project_id=project_id,
            user_id=attacker_id,
        )

    assert exc_info.value.status_code == 404

    assert (
        exc_info.value.detail
        == "Proyecto no encontrado"
    )


def test_project_without_owner_is_not_accessible() -> None:
    project_id = uuid4()

    project = SimpleNamespace(
        id=project_id,
        owner_id=None,
        status="INDEXED",
    )

    db = MagicMock()
    db.get.return_value = project

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        get_project_for_user(
            db=db,
            project_id=project_id,
            user_id=uuid4(),
        )

    assert exc_info.value.status_code == 404


def test_missing_project_for_user_returns_404() -> None:
    db = MagicMock()
    db.get.return_value = None

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        get_project_for_user(
            db=db,
            project_id=uuid4(),
            user_id=uuid4(),
        )

    assert exc_info.value.status_code == 404


def test_indexed_owned_project_is_allowed() -> None:
    user_id = uuid4()
    project_id = uuid4()

    project = SimpleNamespace(
        id=project_id,
        owner_id=user_id,
        status="INDEXED",
    )

    db = MagicMock()
    db.get.return_value = project

    result = get_indexed_project_for_user(
        db=db,
        project_id=project_id,
        user_id=user_id,
    )

    assert result is project


def test_non_indexed_owned_project_returns_409() -> None:
    user_id = uuid4()
    project_id = uuid4()

    project = SimpleNamespace(
        id=project_id,
        owner_id=user_id,
        status="CHUNKED",
    )

    db = MagicMock()
    db.get.return_value = project

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        get_indexed_project_for_user(
            db=db,
            project_id=project_id,
            user_id=user_id,
        )

    assert exc_info.value.status_code == 409


def test_non_owner_gets_404_before_index_status_is_revealed() -> None:
    project = SimpleNamespace(
        id=uuid4(),
        owner_id=uuid4(),
        status="CHUNKED",
    )

    db = MagicMock()
    db.get.return_value = project

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        get_indexed_project_for_user(
            db=db,
            project_id=project.id,
            user_id=uuid4(),
        )

    assert exc_info.value.status_code == 404


def test_conversation_owner_can_access_conversation() -> None:
    user_id = uuid4()
    project_id = uuid4()
    conversation_id = uuid4()

    conversation = SimpleNamespace(
        id=conversation_id,
        project_id=project_id,
    )

    project = SimpleNamespace(
        id=project_id,
        owner_id=user_id,
    )

    db = MagicMock()

    db.get.side_effect = [
        conversation,
        project,
    ]

    result = get_conversation_for_user(
        db=db,
        conversation_id=conversation_id,
        user_id=user_id,
    )

    assert result is conversation


def test_other_user_cannot_access_conversation() -> None:
    owner_id = uuid4()
    attacker_id = uuid4()
    project_id = uuid4()
    conversation_id = uuid4()

    conversation = SimpleNamespace(
        id=conversation_id,
        project_id=project_id,
    )

    project = SimpleNamespace(
        id=project_id,
        owner_id=owner_id,
    )

    db = MagicMock()

    db.get.side_effect = [
        conversation,
        project,
    ]

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        get_conversation_for_user(
            db=db,
            conversation_id=conversation_id,
            user_id=attacker_id,
        )

    assert exc_info.value.status_code == 404

    assert exc_info.value.detail == (
        "Conversación no encontrada"
    )


def test_conversation_without_project_returns_404() -> None:
    conversation_id = uuid4()

    conversation = SimpleNamespace(
        id=conversation_id,
        project_id=uuid4(),
    )

    db = MagicMock()

    db.get.side_effect = [
        conversation,
        None,
    ]

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        get_conversation_for_user(
            db=db,
            conversation_id=conversation_id,
            user_id=uuid4(),
        )

    assert exc_info.value.status_code == 404