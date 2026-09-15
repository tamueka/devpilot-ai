import os
from datetime import (
    UTC,
    datetime,
    timedelta,
)
from uuid import UUID

import jwt
from jwt import InvalidTokenError
from pwdlib import PasswordHash


DEFAULT_JWT_ALGORITHM = "HS256"
DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 60

password_hash = PasswordHash.recommended()


class AuthenticationConfigurationError(
    RuntimeError,
):
    pass


class InvalidAccessTokenError(
    ValueError,
):
    pass


def hash_password(
    password: str,
) -> str:
    if not password:
        raise ValueError(
            "La contraseña no puede estar vacía.",
        )

    return password_hash.hash(
        password,
    )


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    if (
        not plain_password
        or not hashed_password
    ):
        return False

    try:
        return password_hash.verify(
            plain_password,
            hashed_password,
        )
    except Exception:
        return False


def create_access_token(
    user_id: UUID,
) -> str:
    secret_key = _get_jwt_secret_key()
    algorithm = _get_jwt_algorithm()

    now = datetime.now(
        UTC,
    )

    expires_at = (
        now
        + timedelta(
            minutes=(
                _get_access_token_expire_minutes()
            ),
        )
    )

    payload = {
        "sub": str(
            user_id,
        ),
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        secret_key,
        algorithm=algorithm,
    )


def decode_access_token(
    token: str,
) -> UUID:
    if not token:
        raise InvalidAccessTokenError(
            "Token de acceso inválido.",
        )

    try:
        payload = jwt.decode(
            token,
            _get_jwt_secret_key(),
            algorithms=[
                _get_jwt_algorithm(),
            ],
        )

        subject = payload.get(
            "sub",
        )

        if not subject:
            raise InvalidAccessTokenError(
                "Token de acceso inválido.",
            )

        return UUID(
            subject,
        )

    except (
        InvalidTokenError,
        ValueError,
        TypeError,
    ) as exc:
        raise InvalidAccessTokenError(
            "Token de acceso inválido.",
        ) from exc


def _get_jwt_secret_key() -> str:
    secret_key = os.getenv(
        "JWT_SECRET_KEY",
    )

    if not secret_key:
        raise AuthenticationConfigurationError(
            "JWT_SECRET_KEY no está configurada.",
        )

    return secret_key


def _get_jwt_algorithm() -> str:
    algorithm = os.getenv(
        "JWT_ALGORITHM",
        DEFAULT_JWT_ALGORITHM,
    )

    if algorithm != "HS256":
        raise AuthenticationConfigurationError(
            "JWT_ALGORITHM no permitido.",
        )

    return algorithm


def _get_access_token_expire_minutes() -> int:
    raw_value = os.getenv(
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
        str(
            DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES,
        ),
    )

    try:
        minutes = int(
            raw_value,
        )

    except ValueError as exc:
        raise AuthenticationConfigurationError(
            (
                "JWT_ACCESS_TOKEN_EXPIRE_MINUTES "
                "debe ser un entero."
            ),
        ) from exc

    if minutes <= 0:
        raise AuthenticationConfigurationError(
            (
                "JWT_ACCESS_TOKEN_EXPIRE_MINUTES "
                "debe ser mayor que cero."
            ),
        )

    return minutes