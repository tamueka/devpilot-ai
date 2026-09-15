from pathlib import Path
from shutil import rmtree
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from openai import project
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import (
    Project,
    User,
)
from app.schemas.document import DocumentResponse
from app.schemas.project import (
    ProjectCreate,
    ProjectResponse,
)
from app.schemas.unit_test import (
    UnitTestGenerateRequest,
    UnitTestGenerateResponse,
    UnitTestSourceResponse,
)
from app.security.current_user import (
    get_current_user,
)
from app.security.rate_limiter import (
    enforce_generation_rate_limit,
    enforce_upload_rate_limit,
)
from app.security.resource_access import (
    get_document_for_project,
    get_indexed_project_for_user,
    get_project_for_user,
)
from app.security.upload_size import (
    UploadTooLargeError,
    save_stream_with_size_limit,
)
from app.services.project_archive_service import (
    InvalidProjectArchiveError,
    extract_source_files,
)
from app.services.project_chunk_service import (
    create_project_chunks,
)
from app.services.project_document_service import (
    get_project_documents,
    save_project_documents,
)
from app.services.project_embedding_service import (
    EmbeddingConfigurationError,
    create_project_embeddings,
)
from app.services.unit_test_service import (
    generate_document_unit_tests,
)


router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)

UPLOADS_DIR = Path(
    "storage/projects",
)

ALLOWED_ARCHIVE_EXTENSIONS = {
    ".zip",
    ".rar",
}


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user,
    ),
) -> Project:
    project = Project(
        owner_id=current_user.id,
        name=project_data.name,
        description=project_data.description,
        status="CREATED",
    )

    db.add(
        project,
    )

    db.commit()

    db.refresh(
        project,
    )

    return project


@router.get(
    "",
    response_model=list[ProjectResponse],
)
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user,
    ),
) -> list[Project]:
    result = db.execute(
        select(Project)
        .where(
            Project.owner_id
            == current_user.id,
        )
        .order_by(
            Project.created_at.desc(),
        )
    )

    return list(
        result.scalars().all(),
    )


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
)
def get_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user,
    ),
) -> Project:
    return get_project_for_user(
        db=db,
        project_id=project_id,
        user_id=current_user.id,
    )


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user,
    ),
) -> Response:
    project = get_project_for_user(
        db=db,
        project_id=project_id,
        user_id=current_user.id,
    )

    project_directory = (
        UPLOADS_DIR
        / str(project.id)
    )
    try:
        db.delete(
            project,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    if project_directory.exists():
        rmtree(
            project_directory,
            ignore_errors=True,
        )
    return Response(
        status_code=(
            status.HTTP_204_NO_CONTENT
        ),
    )

@router.post(
    "/{project_id}/upload",
    response_model=ProjectResponse,
)
async def upload_project(
    project_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user,
    ),
    _rate_limit: None = Depends(
        enforce_upload_rate_limit,
    ),
) -> Project:
    project = get_project_for_user(
        db=db,
        project_id=project_id,
        user_id=current_user.id,
    )

    filename = Path(
        file.filename or "",
    ).name

    archive_extension = (
        Path(filename).suffix.lower()
    )

    if (
        not filename
        or archive_extension
        not in ALLOWED_ARCHIVE_EXTENSIONS
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "El archivo debe tener extensión "
                ".zip o .rar."
            ),
        )

    project_directory = (
        UPLOADS_DIR
        / str(project_id)
    )

    project_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    archive_path = (
        project_directory
        / filename
    )

    source_directory = (
        project_directory
        / "source"
    )

    try:
        file.file.seek(
            0,
        )

        save_stream_with_size_limit(
            source=file.file,
            destination_path=archive_path,
        )

    except UploadTooLargeError as exc:
        archive_path.unlink(
            missing_ok=True,
        )

        raise HTTPException(
            status_code=(
                status.HTTP_413_CONTENT_TOO_LARGE
            ),
            detail=(
                "El archivo comprimido supera "
                "el tamaño máximo permitido "
                "de 50 MB."
            ),
        ) from exc

    finally:
        await file.close()

    # Eliminamos una extracción anterior
    # antes de volver a indexar.
    if source_directory.exists():
        rmtree(
            source_directory,
        )

    try:
        extracted_files = (
            extract_source_files(
                archive_path=archive_path,
                destination_dir=source_directory,
            )
        )

    except InvalidProjectArchiveError as exc:
        archive_path.unlink(
            missing_ok=True,
        )

        if source_directory.exists():
            rmtree(
                source_directory,
            )

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(
                exc,
            ),
        ) from exc

    if not extracted_files:
        archive_path.unlink(
            missing_ok=True,
        )

        if source_directory.exists():
            rmtree(
                source_directory,
            )

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "El archivo comprimido no contiene "
                "archivos de código compatibles."
            ),
        )
        
    try:
        previous_archive = (
            Path(project.uploaded_file)
            if project.uploaded_file
            else None
        )

        if (
            previous_archive
            and previous_archive != archive_path
        ):
            previous_archive.unlink(
                missing_ok=True,
            )

        project.uploaded_file = str(
            archive_path,
        )

        project.status = "EXTRACTED"

        save_project_documents(
            db=db,
            project_id=project.id,
            source_directory=source_directory,
            extracted_files=extracted_files,
        )

        project.status = (
            "INDEXED_FILES"
        )

        create_project_chunks(
            db=db,
            project_id=project.id,
        )

        project.status = "CHUNKED"

        create_project_embeddings(
            db=db,
            project_id=project.id,
        )

        project.status = "INDEXED"

        db.commit()

        db.refresh(
            project,
        )

        return project

    except EmbeddingConfigurationError as exc:
        db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "El servicio de IA "
                "no está disponible."
            ),
        ) from exc

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise


@router.get(
    "/{project_id}/documents",
    response_model=list[DocumentResponse],
)
def list_project_documents(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user,
    ),
) -> list:
    project = (
        get_indexed_project_for_user(
            db=db,
            project_id=project_id,
            user_id=current_user.id,
            conflict_detail=(
                "El proyecto debe estar indexado "
                "para consultar sus archivos."
            ),
        )
    )

    return get_project_documents(
        db=db,
        project_id=project.id,
    )


@router.post(
    "/{project_id}/unit-tests",
    response_model=UnitTestGenerateResponse,
)
def generate_unit_tests(
    project_id: UUID,
    request: UnitTestGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user,
    ),
    _rate_limit: None = Depends(
        enforce_generation_rate_limit,
    ),
) -> UnitTestGenerateResponse:
    project = get_project_for_user(
        db=db,
        project_id=project_id,
        user_id=current_user.id,
    )

    if project.id != request.project_id:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "El project_id de la URL no coincide "
                "con el project_id de la petición."
            ),
        )

    project = (
        get_indexed_project_for_user(
            db=db,
            project_id=project.id,
            user_id=current_user.id,
            conflict_detail=(
                "El proyecto debe estar completamente "
                "indexado para generar tests."
            ),
        )
    )

    get_document_for_project(
        db=db,
        document_id=request.document_id,
        project_id=project.id,
    )

    try:
        result = (
            generate_document_unit_tests(
                db=db,
                project_id=project.id,
                document_id=(
                    request.document_id
                ),
                framework=(
                    request.framework
                ),
            )
        )

    except EmbeddingConfigurationError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "El servicio de IA "
                "no está disponible."
            ),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_CONTENT
            ),
            detail=str(
                exc,
            ),
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "No se pudieron generar "
                "los tests unitarios."
            ),
        ) from exc

    return UnitTestGenerateResponse(
        content=result.content,
        suggested_filename=(
            result.suggested_filename
        ),
        sources=[
            UnitTestSourceResponse(
                path=source.path,
                language=source.language,
            )
            for source in result.sources
        ],
    )
