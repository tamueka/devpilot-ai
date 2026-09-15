from __future__ import annotations
import stat
from pathlib import Path, PurePosixPath
from typing import BinaryIO
from zipfile import (
    BadZipFile,
    ZipFile,
    ZipInfo,
    is_zipfile,
)

import rarfile

def _configure_rar_backend() -> None:
    seven_zip_path = Path(
        r"C:\Program Files\7-Zip\7z.exe"
    )

    if not seven_zip_path.exists():
        return

    rarfile.SEVENZIP_TOOL = str(
        seven_zip_path,
    )

    rarfile.tool_setup(
        unrar=False,
        unar=False,
        bsdtar=False,
        sevenzip=True,
        sevenzip2=False,
        force=True,
    )


_configure_rar_backend()

ALLOWED_EXTENSIONS = {
    ".ts",
    ".js",
    ".jsx",
    ".tsx",
    ".py",
    ".java",
    ".cs",
    ".go",
    ".html",
    ".css",
    ".scss",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".xml",
}

EXCLUDED_DIRECTORIES = {
    ".git",
    ".idea",
    ".vscode",
    ".angular",
    ".next",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "target",
}

EXCLUDED_FILES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "bun.lock",
    "bun.lockb",
    "poetry.lock",
}

MAX_FILES = 5_000

MAX_FILE_SIZE = (
    5
    * 1024
    * 1024
)

MAX_TOTAL_SIZE = (
    100
    * 1024
    * 1024
)

COPY_CHUNK_SIZE = (
    1024
    * 1024
)


class InvalidProjectArchiveError(
    ValueError,
):
    pass


def extract_source_files(
    archive_path: Path,
    destination_dir: Path,
) -> list[Path]:
    archive_format = _get_archive_format(
        archive_path,
    )

    destination_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    if archive_format == "zip":
        return _extract_zip_source_files(
            archive_path=archive_path,
            destination_dir=destination_dir,
        )

    return _extract_rar_source_files(
        archive_path=archive_path,
        destination_dir=destination_dir,
    )


def _get_archive_format(
    archive_path: Path,
) -> str:
    suffix = archive_path.suffix.lower()

    if suffix == ".zip":
        if not is_zipfile(archive_path):
            raise InvalidProjectArchiveError(
                "El archivo no es un ZIP válido.",
            )

        return "zip"

    if suffix == ".rar":
        if not rarfile.is_rarfile(
            archive_path,
        ):
            raise InvalidProjectArchiveError(
                "El archivo no es un RAR válido.",
            )

        return "rar"

    raise InvalidProjectArchiveError(
        "El archivo debe tener extensión "
        ".zip o .rar.",
    )


def _extract_zip_source_files(
    archive_path: Path,
    destination_dir: Path,
) -> list[Path]:
    try:
        with ZipFile(
            archive_path,
            mode="r",
        ) as archive:
            members = [
                info
                for info in archive.infolist()
                if not info.is_dir()
            ]

            _validate_file_count(
                len(members),
            )

            extracted_files: list[Path] = []
            total_size = 0

            for info in members:
                if _is_zip_symlink(info):
                    raise InvalidProjectArchiveError(
                        "El archivo ZIP contiene "
                        "enlaces simbólicos no permitidos.",
                    )

                relative_path = (
                    _get_safe_relative_path(
                        info.filename,
                    )
                )

                if not _is_allowed_source_file(
                    relative_path,
                ):
                    continue

                _validate_declared_file_size(
                    info.file_size,
                )

                total_size = (
                    _validate_declared_total_size(
                        current_total=total_size,
                        file_size=info.file_size,
                    )
                )

                destination_path = (
                    _get_destination_path(
                        destination_dir,
                        relative_path,
                    )
                )

                destination_path.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                with archive.open(
                    info,
                    mode="r",
                ) as source:
                    written_size = (
                        _copy_member_safely(
                            source=source,
                            destination_path=(
                                destination_path
                            ),
                            total_size_before=(
                                total_size
                                - info.file_size
                            ),
                        )
                    )

                total_size = (
                    total_size
                    - info.file_size
                    + written_size
                )

                extracted_files.append(
                    destination_path,
                )

            return extracted_files

    except BadZipFile as exc:
        raise InvalidProjectArchiveError(
            "El archivo ZIP está dañado "
            "o no es válido.",
        ) from exc


def _extract_rar_source_files(
    archive_path: Path,
    destination_dir: Path,
) -> list[Path]:
    try:
        with rarfile.RarFile(
            archive_path,
            mode="r",
            errors="strict",
        ) as archive:
            if archive.needs_password():
                raise InvalidProjectArchiveError(
                    "Los archivos RAR protegidos "
                    "con contraseña no están permitidos.",
                )

            volumes = archive.volumelist()

            if len(volumes) > 1:
                raise InvalidProjectArchiveError(
                    "Los archivos RAR multipart "
                    "no están permitidos.",
                )

            members = [
                info
                for info in archive.infolist()
                if not info.is_dir()
            ]

            _validate_file_count(
                len(members),
            )

            extracted_files: list[Path] = []
            total_size = 0

            for info in members:
                if _is_unsafe_rar_member(
                    info,
                ):
                    raise InvalidProjectArchiveError(
                        "El archivo RAR contiene "
                        "enlaces o entradas "
                        "no permitidas.",
                    )

                relative_path = (
                    _get_safe_relative_path(
                        info.filename,
                    )
                )

                if not _is_allowed_source_file(
                    relative_path,
                ):
                    continue

                _validate_declared_file_size(
                    info.file_size,
                )

                total_size = (
                    _validate_declared_total_size(
                        current_total=total_size,
                        file_size=info.file_size,
                    )
                )

                destination_path = (
                    _get_destination_path(
                        destination_dir,
                        relative_path,
                    )
                )

                destination_path.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                try:
                    with archive.open(
                        info,
                        mode="r",
                    ) as source:
                        written_size = (
                            _copy_member_safely(
                                source=source,
                                destination_path=(
                                    destination_path
                                ),
                                total_size_before=(
                                    total_size
                                    - info.file_size
                                ),
                            )
                        )

                except rarfile.RarCannotExec as exc:
                    raise InvalidProjectArchiveError(
                        "No se puede descomprimir "
                        "el archivo RAR porque no "
                        "hay un extractor RAR "
                        "disponible en el sistema.",
                    ) from exc

                total_size = (
                    total_size
                    - info.file_size
                    + written_size
                )

                extracted_files.append(
                    destination_path,
                )

            return extracted_files

    except InvalidProjectArchiveError:
        raise

    except rarfile.PasswordRequired as exc:
        raise InvalidProjectArchiveError(
            "Los archivos RAR protegidos "
            "con contraseña no están permitidos.",
        ) from exc

    except rarfile.RarCannotExec as exc:
        raise InvalidProjectArchiveError(
            "No se puede descomprimir el archivo "
            "RAR porque no hay un extractor RAR "
            "disponible en el sistema.",
        ) from exc

    except rarfile.Error as exc:
        raise InvalidProjectArchiveError(
            "El archivo RAR está dañado "
            "o no es válido.",
        ) from exc


def _get_safe_relative_path(
    filename: str,
) -> PurePosixPath:
    normalized_filename = (
        filename
        .replace("\\", "/")
        .strip()
    )

    if (
        not normalized_filename
        or "\x00" in normalized_filename
    ):
        raise InvalidProjectArchiveError(
            "El archivo comprimido contiene "
            "una ruta inválida.",
        )

    path = PurePosixPath(
        normalized_filename,
    )

    if path.is_absolute():
        raise InvalidProjectArchiveError(
            "El archivo comprimido contiene "
            "rutas absolutas no permitidas.",
        )

    if any(
        part in {
            "",
            ".",
            "..",
        }
        for part in path.parts
    ):
        raise InvalidProjectArchiveError(
            "El archivo comprimido contiene "
            "rutas inseguras.",
        )

    if any(
        ":" in part
        for part in path.parts
    ):
        raise InvalidProjectArchiveError(
            "El archivo comprimido contiene "
            "rutas no permitidas.",
        )

    return path


def _get_destination_path(
    destination_dir: Path,
    relative_path: PurePosixPath,
) -> Path:
    root = destination_dir.resolve()

    destination_path = (
        destination_dir.joinpath(
            *relative_path.parts,
        )
    )

    resolved_parent = (
        destination_path.parent.resolve()
    )

    if not resolved_parent.is_relative_to(
        root,
    ):
        raise InvalidProjectArchiveError(
            "El archivo comprimido intenta "
            "escribir fuera del directorio "
            "permitido.",
        )

    return destination_path


def _is_allowed_source_file(
    path: PurePosixPath,
) -> bool:
    if path.name in EXCLUDED_FILES:
        return False

    directory_parts = {
        part.lower()
        for part in path.parts[:-1]
    }

    excluded_directories = {
        directory.lower()
        for directory in EXCLUDED_DIRECTORIES
    }

    if (
        directory_parts
        & excluded_directories
    ):
        return False

    return (
        path.suffix.lower()
        in ALLOWED_EXTENSIONS
    )


def _is_zip_symlink(
    info: ZipInfo,
) -> bool:
    unix_mode = (
        info.external_attr
        >> 16
    )

    return stat.S_ISLNK(
        unix_mode,
    )


def _is_unsafe_rar_member(
    info: rarfile.RarInfo,
) -> bool:
    if info.is_symlink():
        return True

    if getattr(
        info,
        "file_redir",
        None,
    ) is not None:
        return True

    return not info.is_file()


def _validate_file_count(
    file_count: int,
) -> None:
    if file_count > MAX_FILES:
        raise InvalidProjectArchiveError(
            "El archivo comprimido contiene "
            f"más de {MAX_FILES} archivos.",
        )


def _validate_declared_file_size(
    file_size: int,
) -> None:
    if file_size < 0:
        raise InvalidProjectArchiveError(
            "El archivo comprimido contiene "
            "un tamaño de archivo inválido.",
        )

    if file_size > MAX_FILE_SIZE:
        raise InvalidProjectArchiveError(
            "Uno de los archivos supera "
            "el tamaño máximo permitido "
            "de 5 MB.",
        )


def _validate_declared_total_size(
    current_total: int,
    file_size: int,
) -> int:
    new_total = (
        current_total
        + file_size
    )

    if new_total > MAX_TOTAL_SIZE:
        raise InvalidProjectArchiveError(
            "El contenido descomprimido supera "
            "el tamaño máximo permitido "
            "de 100 MB.",
        )

    return new_total


def _copy_member_safely(
    source: BinaryIO,
    destination_path: Path,
    total_size_before: int,
) -> int:
    written_size = 0

    try:
        with destination_path.open(
            mode="wb",
        ) as destination:
            while True:
                chunk = source.read(
                    COPY_CHUNK_SIZE,
                )

                if not chunk:
                    break

                written_size += len(chunk)

                if (
                    written_size
                    > MAX_FILE_SIZE
                ):
                    raise InvalidProjectArchiveError(
                        "Uno de los archivos supera "
                        "el tamaño máximo permitido "
                        "de 5 MB.",
                    )

                if (
                    total_size_before
                    + written_size
                    > MAX_TOTAL_SIZE
                ):
                    raise InvalidProjectArchiveError(
                        "El contenido descomprimido "
                        "supera el tamaño máximo "
                        "permitido de 100 MB.",
                    )

                destination.write(
                    chunk,
                )

    except Exception:
        destination_path.unlink(
            missing_ok=True,
        )
        raise

    return written_size
