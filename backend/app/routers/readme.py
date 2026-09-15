from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.schemas.readme import (
    ReadmeGenerateRequest,
    ReadmeGenerateResponse,
    ReadmeSourceResponse,
)
from app.security.rate_limiter import (
    enforce_generation_rate_limit,
)
from app.security.resource_access import (
    get_project_or_404,
)
from app.services.project_embedding_service import (
    EmbeddingConfigurationError,
)
from app.services.readme_service import (
    generate_project_readme,
)
from app.security.current_user import (
    get_current_user,
)

from app.security.resource_access import (
    get_indexed_project_for_user,
)


router = APIRouter(
    tags=["README"],
)


@router.post(
    "/projects/{project_id}/readme",
    response_model=ReadmeGenerateResponse,
)
def generate_readme(
    project_id: UUID,
    request: ReadmeGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user,
    ),
    _rate_limit: None = Depends(
        enforce_generation_rate_limit,
    ),
) -> ReadmeGenerateResponse:
    project = get_project_or_404(
        db=db,
        project_id=project_id,
    )

    if project.id != request.project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "El project_id de la URL no coincide "
                "con el project_id de la petición."
            ),
        )

    project = get_indexed_project_for_user(
        db=db,
        project_id=project.id,
        user_id=current_user.id,
        conflict_detail=(
            "El proyecto debe estar completamente "
            "indexado para generar el README."
        ),
    )

    try:
        result = generate_project_readme(
            db=db,
            project_id=project.id,
            language=request.language,
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
                "No se pudo generar "
                "el README."
            ),
        ) from exc

    return ReadmeGenerateResponse(
        content=result.content,
        sources=[
            ReadmeSourceResponse(
                path=source.path,
                language=source.language,
            )
            for source in result.sources
        ],
    )