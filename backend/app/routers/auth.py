from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.security.auth import (
    AuthenticationConfigurationError,
    create_access_token,
)
from app.security.current_user import (
    get_current_user,
)
from app.services.user_service import (
    authenticate_user,
    create_user,
    get_user_by_email,
)


router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
) -> UserResponse:
    existing_user = get_user_by_email(
        db=db,
        email=str(
            request.email,
        ),
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Ya existe un usuario "
                "con ese email."
            ),
        )

    try:
        user = create_user(
            db=db,
            email=str(
                request.email,
            ),
            password=request.password,
        )

        db.commit()

        db.refresh(
            user,
        )

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Ya existe un usuario "
                "con ese email."
            ),
        ) from exc

    return UserResponse.model_validate(
        user,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = authenticate_user(
        db=db,
        email=str(
            request.email,
        ),
        password=request.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    try:
        access_token = create_access_token(
            user.id,
        )

    except AuthenticationConfigurationError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "El servicio de autenticación "
                "no está disponible."
            ),
        ) from exc

    return TokenResponse(
        access_token=access_token,
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
def me(
    current_user: User = Depends(
        get_current_user,
    ),
) -> UserResponse:
    return UserResponse.model_validate(
        current_user,
    )