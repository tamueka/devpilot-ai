from fastapi import (
    Depends,
    HTTPException,
    status,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.security.auth import (
    AuthenticationConfigurationError,
    InvalidAccessTokenError,
    decode_access_token,
)


bearer_scheme = HTTPBearer(
    auto_error=False,
)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas.",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme,
    ),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise _unauthorized()

    if credentials.scheme.lower() != "bearer":
        raise _unauthorized()

    try:
        user_id = decode_access_token(
            credentials.credentials,
        )

    except InvalidAccessTokenError as exc:
        raise _unauthorized() from exc

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

    user = db.get(
        User,
        user_id,
    )

    if user is None:
        raise _unauthorized()

    if not user.is_active:
        raise _unauthorized()

    return user