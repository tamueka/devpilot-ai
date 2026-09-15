from pathlib import Path
from unittest.mock import MagicMock
from uuid import uuid4

from app.services.project_document_service import (
    save_project_documents,
)


def create_file(
    root: Path,
    relative_path: str,
    content: str,
) -> Path:
    file_path = (
        root
        / relative_path
    )

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path.write_text(
        content,
        encoding="utf-8",
    )

    return file_path


def test_env_file_is_not_indexed(
    tmp_path: Path,
) -> None:
    db = MagicMock()
    project_id = uuid4()

    env_file = create_file(
        root=tmp_path,
        relative_path=".env",
        content=(
            "DATABASE_URL="
            "postgresql://user:password@localhost/db"
        ),
    )

    documents = save_project_documents(
        db=db,
        project_id=project_id,
        source_directory=tmp_path,
        extracted_files=[
            env_file,
        ],
    )

    assert documents == []

    db.add_all.assert_not_called()
    db.flush.assert_called_once()


def test_source_file_with_openai_key_is_not_indexed(
    tmp_path: Path,
) -> None:
    db = MagicMock()
    project_id = uuid4()

    source_file = create_file(
        root=tmp_path,
        relative_path="src/config.ts",
        content=(
            "export const apiKey = "
            "'sk-proj-"
            "abcdefghijklmnopqrstuvwxyz123456';"
        ),
    )

    documents = save_project_documents(
        db=db,
        project_id=project_id,
        source_directory=tmp_path,
        extracted_files=[
            source_file,
        ],
    )

    assert documents == []

    db.add_all.assert_not_called()


def test_private_key_is_not_indexed(
    tmp_path: Path,
) -> None:
    db = MagicMock()
    project_id = uuid4()

    source_file = create_file(
        root=tmp_path,
        relative_path="src/key.txt",
        content=(
            "-----BEGIN PRIVATE KEY-----\n"
            "secret\n"
            "-----END PRIVATE KEY-----"
        ),
    )

    documents = save_project_documents(
        db=db,
        project_id=project_id,
        source_directory=tmp_path,
        extracted_files=[
            source_file,
        ],
    )

    assert documents == []

    db.add_all.assert_not_called()


def test_normal_source_file_is_indexed(
    tmp_path: Path,
) -> None:
    db = MagicMock()
    project_id = uuid4()

    source_file = create_file(
        root=tmp_path,
        relative_path="src/app.ts",
        content=(
            "export const app = "
            "'DevPilot';"
        ),
    )

    documents = save_project_documents(
        db=db,
        project_id=project_id,
        source_directory=tmp_path,
        extracted_files=[
            source_file,
        ],
    )

    assert len(
        documents,
    ) == 1

    document = documents[0]

    assert (
        document.project_id
        == project_id
    )

    assert (
        document.path
        == "src/app.ts"
    )

    assert (
        document.filename
        == "app.ts"
    )

    assert (
        document.extension
        == ".ts"
    )

    assert (
        document.language
        == "typescript"
    )

    assert (
        document.content
        == "export const app = 'DevPilot';"
    )

    db.add_all.assert_called_once_with(
        documents,
    )


def test_env_example_without_real_secret_can_be_indexed(
    tmp_path: Path,
) -> None:
    db = MagicMock()
    project_id = uuid4()

    env_example = create_file(
        root=tmp_path,
        relative_path=".env.example",
        content=(
            "OPENAI_API_KEY=\n"
            "DATABASE_URL="
            "postgresql://localhost/devpilot_ai"
        ),
    )

    documents = save_project_documents(
        db=db,
        project_id=project_id,
        source_directory=tmp_path,
        extracted_files=[
            env_example,
        ],
    )

    assert len(
        documents,
    ) == 1

    assert (
        documents[0].path
        == ".env.example"
    )


def test_only_safe_files_are_added_to_database(
    tmp_path: Path,
) -> None:
    db = MagicMock()
    project_id = uuid4()

    safe_file = create_file(
        root=tmp_path,
        relative_path="src/app.ts",
        content=(
            "export class App {}"
        ),
    )

    secret_file = create_file(
        root=tmp_path,
        relative_path="src/secrets.ts",
        content=(
            "const apiKey = "
            "'sk-proj-"
            "abcdefghijklmnopqrstuvwxyz123456';"
        ),
    )

    env_file = create_file(
        root=tmp_path,
        relative_path=".env",
        content=(
            "SECRET=value"
        ),
    )

    documents = save_project_documents(
        db=db,
        project_id=project_id,
        source_directory=tmp_path,
        extracted_files=[
            safe_file,
            secret_file,
            env_file,
        ],
    )

    assert len(
        documents,
    ) == 1

    assert (
        documents[0].path
        == "src/app.ts"
    )

    added_documents = (
        db.add_all.call_args.args[0]
    )

    assert len(
        added_documents,
    ) == 1

    assert (
        added_documents[0].path
        == "src/app.ts"
    )