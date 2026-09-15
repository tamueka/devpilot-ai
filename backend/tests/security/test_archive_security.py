from pathlib import Path
from zipfile import ZipFile, ZipInfo
import pytest
from app.services import project_archive_service as archive_service


def create_zip(
    path: Path,
    files: dict[str, bytes],
) -> Path:
    with ZipFile(
        path,
        "w",
    ) as archive:
        for filename, content in files.items():
            archive.writestr(
                filename,
                content,
            )

    return path


def test_extracts_valid_source_file(
    tmp_path: Path,
) -> None:
    zip_path = create_zip(
        tmp_path / "project.zip",
        {
            "src/app.ts": (
                b"export const app = true;"
            ),
        },
    )

    destination = (
        tmp_path / "extracted"
    )

    archive_service.extract_source_files(
        zip_path,
        destination,
    )

    extracted_file = (
        destination
        / "src"
        / "app.ts"
    )

    assert extracted_file.exists()

    assert extracted_file.read_text(
        encoding="utf-8",
    ) == "export const app = true;"


def test_blocks_parent_directory_traversal(
    tmp_path: Path,
) -> None:
    zip_path = create_zip(
        tmp_path / "traversal.zip",
        {
            "../evil.ts": b"malicious",
            "src/safe.ts": b"safe",
        },
    )

    destination = (
        tmp_path / "extracted"
    )

    with pytest.raises(
        archive_service.InvalidProjectArchiveError,
        match="rutas inseguras",
    ):
        archive_service.extract_source_files(
            zip_path,
            destination,
        )

    assert not (
        tmp_path / "evil.ts"
    ).exists()



def test_blocks_nested_parent_directory_traversal(
    tmp_path: Path,
) -> None:
    zip_path = create_zip(
        tmp_path / "nested-traversal.zip",
        {
            "src/../../evil.py":
                b"print('evil')",
        },
    )

    destination = (
        tmp_path / "extracted"
    )

    with pytest.raises(
        archive_service.InvalidProjectArchiveError,
        match="rutas inseguras",
    ):
        archive_service.extract_source_files(
            zip_path,
            destination,
        )

    assert not (
        tmp_path / "evil.py"
    ).exists()



def test_blocks_absolute_paths(
    tmp_path: Path,
) -> None:
    zip_path = create_zip(
        tmp_path / "absolute.zip",
        {
            "/evil.ts": b"malicious",
            "safe.ts": b"safe",
        },
    )

    destination = (
        tmp_path / "extracted"
    )

    with pytest.raises(
        archive_service.InvalidProjectArchiveError,
        match="rutas absolutas",
    ):
        archive_service.extract_source_files(
            zip_path,
            destination,
        )


def test_ignores_disallowed_extensions(
    tmp_path: Path,
) -> None:
    zip_path = create_zip(
        tmp_path / "extensions.zip",
        {
            "src/app.ts": (
                b"export const app = true;"
            ),
            "malware.exe": (
                b"fake executable"
            ),
            "image.png": (
                b"fake image"
            ),
            "document.pdf": (
                b"fake pdf"
            ),
        },
    )

    destination = (
        tmp_path / "extracted"
    )

    archive_service.extract_source_files(
        zip_path,
        destination,
    )

    assert (
        destination
        / "src"
        / "app.ts"
    ).exists()

    assert not (
        destination
        / "malware.exe"
    ).exists()

    assert not (
        destination
        / "image.png"
    ).exists()

    assert not (
        destination
        / "document.pdf"
    ).exists()


def test_ignores_node_modules(
    tmp_path: Path,
) -> None:
    zip_path = create_zip(
        tmp_path / "node-modules.zip",
        {
            "src/app.ts": (
                b"export const app = true;"
            ),
            "node_modules/package/index.js": (
                b"dependency"
            ),
        },
    )

    destination = (
        tmp_path / "extracted"
    )

    archive_service.extract_source_files(
        zip_path,
        destination,
    )

    assert (
        destination
        / "src"
        / "app.ts"
    ).exists()

    assert not (
        destination
        / "node_modules"
        / "package"
        / "index.js"
    ).exists()


def test_ignores_git_directory(
    tmp_path: Path,
) -> None:
    zip_path = create_zip(
        tmp_path / "git.zip",
        {
            ".git/config": (
                b"[core]"
            ),
            "src/app.ts": (
                b"safe"
            ),
        },
    )

    destination = (
        tmp_path / "extracted"
    )

    archive_service.extract_source_files(
        zip_path,
        destination,
    )

    assert not (
        destination
        / ".git"
        / "config"
    ).exists()

    assert (
        destination
        / "src"
        / "app.ts"
    ).exists()


def test_ignores_lock_files(
    tmp_path: Path,
) -> None:
    zip_path = create_zip(
        tmp_path / "locks.zip",
        {
            "package-lock.json": (
                b'{"lockfileVersion": 3}'
            ),
            "src/app.ts": (
                b"safe"
            ),
        },
    )

    destination = (
        tmp_path / "extracted"
    )

    archive_service.extract_source_files(
        zip_path,
        destination,
    )

    assert not (
        destination
        / "package-lock.json"
    ).exists()

    assert (
        destination
        / "src"
        / "app.ts"
    ).exists()


def test_ignores_symbolic_links(
    tmp_path: Path,
) -> None:
    zip_path = (
        tmp_path / "symlink.zip"
    )

    with ZipFile(
        zip_path,
        "w",
    ) as archive:
        symlink = ZipInfo(
            "src/link.ts",
        )

        symlink.create_system = 3

        symlink.external_attr = (
            0o120777 << 16
        )

        archive.writestr(
            symlink,
            "../../outside.ts",
        )

        archive.writestr(
            "src/safe.ts",
            "safe",
        )

    destination = (
        tmp_path / "extracted"
    )

    with pytest.raises(
        archive_service.InvalidProjectArchiveError,
        match="enlaces simbólicos",
    ):
        archive_service.extract_source_files(
            zip_path,
            destination,
        )

    assert not (
        tmp_path / "outside.ts"
    ).exists()


def test_rejects_archive_with_too_many_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        archive_service,
        "MAX_FILES",
        2,
    )

    zip_path = create_zip(
        tmp_path / "too-many.zip",
        {
            "one.ts": b"1",
            "two.ts": b"2",
            "three.ts": b"3",
        },
    )

    destination = (
        tmp_path / "extracted"
    )

    with pytest.raises(
        archive_service.InvalidProjectArchiveError,
    ):
        archive_service.extract_source_files(
            zip_path,
            destination,
        )


def test_skips_file_exceeding_max_file_size(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        archive_service,
        "MAX_FILE_SIZE",
        10,
    )

    zip_path = create_zip(
        tmp_path / "large-file.zip",
        {
            "large.ts": b"A" * 20,
            "safe.ts": b"safe",
        },
    )

    destination = (
        tmp_path / "extracted"
    )

    with pytest.raises(
        archive_service.InvalidProjectArchiveError,
        match="tamaño máximo",
    ):
        archive_service.extract_source_files(
            zip_path,
            destination,
        )


def test_rejects_archive_exceeding_total_size(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        archive_service,
        "MAX_TOTAL_SIZE",
        15,
    )

    zip_path = create_zip(
        tmp_path / "zip-bomb.zip",
        {
            "one.ts": (
                b"A" * 10
            ),
            "two.ts": (
                b"B" * 10
            ),
        },
    )

    destination = (
        tmp_path / "extracted"
    )

    with pytest.raises(
        archive_service.InvalidProjectArchiveError,
    ):
        archive_service.extract_source_files(
            zip_path,
            destination,
        )