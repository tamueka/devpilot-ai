from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import (
    Conversation,
    Document,
    Project,
)


DEFAULT_PROJECT_NOT_INDEXED_DETAIL = (
    "El proyecto todavía no está completamente indexado."
)


def get_project_or_404(
    db: Session,
    project_id: UUID,
) -> Project:
    project = db.get(
        Project,
        project_id,
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado",
        )

    return project


def get_project_for_user(
    db: Session,
    project_id: UUID,
    user_id: UUID,
) -> Project:
    project = db.get(
        Project,
        project_id,
    )

    if (
        project is None
        or project.owner_id != user_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado",
        )

    return project


def get_indexed_project(
    db: Session,
    project_id: UUID,
    conflict_detail: str = DEFAULT_PROJECT_NOT_INDEXED_DETAIL,
) -> Project:
    project = get_project_or_404(
        db=db,
        project_id=project_id,
    )

    if project.status != "INDEXED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=conflict_detail,
        )

    return project


def get_indexed_project_for_user(
    db: Session,
    project_id: UUID,
    user_id: UUID,
    conflict_detail: str = DEFAULT_PROJECT_NOT_INDEXED_DETAIL,
) -> Project:
    project = get_project_for_user(
        db=db,
        project_id=project_id,
        user_id=user_id,
    )

    if project.status != "INDEXED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=conflict_detail,
        )

    return project


def get_conversation_or_404(
    db: Session,
    conversation_id: UUID,
) -> Conversation:
    conversation = db.get(
        Conversation,
        conversation_id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversación no encontrada",
        )

    return conversation


def get_conversation_for_project(
    db: Session,
    conversation_id: UUID,
    project_id: UUID,
) -> Conversation:
    conversation = get_conversation_or_404(
        db=db,
        conversation_id=conversation_id,
    )

    if conversation.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "La conversación no pertenece "
                "al proyecto indicado."
            ),
        )

    return conversation


def get_conversation_for_user(
    db: Session,
    conversation_id: UUID,
    user_id: UUID,
) -> Conversation:
    conversation = get_conversation_or_404(
        db=db,
        conversation_id=conversation_id,
    )

    project = db.get(
        Project,
        conversation.project_id,
    )

    if (
        project is None
        or project.owner_id != user_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversación no encontrada",
        )

    return conversation


def get_document_for_project(
    db: Session,
    document_id: UUID,
    project_id: UUID,
) -> Document:
    document = db.get(
        Document,
        document_id,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo no encontrado",
        )

    if document.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo no encontrado",
        )

    return document