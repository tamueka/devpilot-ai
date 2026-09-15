from pathlib import Path
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import Document
from app.security.sensitive_content import (
    contains_sensitive_content,
    is_sensitive_path,
)


LANGUAGE_BY_EXTENSION = {
    ".ts": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".py": "python",
    ".java": "java",
    ".cs": "csharp",
    ".go": "go",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".md": "markdown",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".xml": "xml",
}


def save_project_documents(
    db: Session,
    project_id: UUID,
    source_directory: Path,
    extracted_files: list[Path],
) -> list[Document]:
    _delete_existing_documents(
        db=db,
        project_id=project_id,
    )

    documents: list[Document] = []

    for file_path in extracted_files:
        document = _create_document_if_safe(
            project_id=project_id,
            source_directory=source_directory,
            file_path=file_path,
        )

        if document is not None:
            documents.append(
                document,
            )

    if documents:
        db.add_all(
            documents,
        )

    db.flush()

    return documents


def _delete_existing_documents(
    db: Session,
    project_id: UUID,
) -> None:
    db.execute(
        delete(Document).where(
            Document.project_id
            == project_id,
        ),
    )


def _create_document_if_safe(
    project_id: UUID,
    source_directory: Path,
    file_path: Path,
) -> Document | None:
    relative_path = file_path.relative_to(
        source_directory,
    )

    document_path = (
        relative_path.as_posix()
    )

    if is_sensitive_path(
        document_path,
    ):
        return None

    content = file_path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    if contains_sensitive_content(
        content,
    ):
        return None

    extension = (
        file_path.suffix.lower()
    )

    return Document(
        project_id=project_id,
        path=document_path,
        filename=file_path.name,
        extension=extension,
        language=LANGUAGE_BY_EXTENSION.get(
            extension,
            "unknown",
        ),
        size=file_path.stat().st_size,
        content=content,
    )


def get_project_documents(
    db: Session,
    project_id: UUID,
) -> list[Document]:
    result = db.execute(
        select(Document)
        .where(
            Document.project_id
            == project_id,
        )
        .order_by(
            Document.path.asc(),
        )
    )

    return list(
        result.scalars().all(),
    )