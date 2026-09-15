from types import SimpleNamespace
from unittest.mock import (
    MagicMock,
    patch,
)
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.security import (
    HTTPAuthorizationCredentials,
)

from app.security.current_user import (
    get_current_user,
)


def create_credentials(
    token: str = "token",
) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )


def test_current_user_is_returned() -> None:
    user_id = uuid4()

    user = SimpleNamespace(
        id=user_id,
        is_active=True,
    )

    db = MagicMock()
    db.get.return_value = user

    with patch(
        "app.security.current_user."
        "decode_access_token",
        return_value=user_id,
    ):
        result = get_current_user(
            credentials=create_credentials(),
            db=db,
        )

    assert result is user


def test_missing_credentials_returns_401() -> None:
    db = MagicMock()

    with pytest.raises(
        HTTPException,
    ) as exc_info:
        get_current_user(
            credentials=None,
            db=db,
        )

    assert (
        exc_info.value.status_code
        == 401
    )


def test_invalid_token_returns_401() -> None:
    from app.security.auth import (
        InvalidAccessTokenError,
    )

    db = MagicMock()

    with patch(
        "app.security.current_user."
        "decode_access_token",
        side_effect=InvalidAccessTokenError(
            "invalid",
        ),
    ):
        with pytest.raises(
            HTTPException,
        ) as exc_info:
            get_current_user(
                credentials=(
                    create_credentials()
                ),
                db=db,
            )

    assert (
        exc_info.value.status_code
        == 401
    )


def test_unknown_user_returns_401() -> None:
    user_id = uuid4()

    db = MagicMock()
    db.get.return_value = None

    with patch(
        "app.security.current_user."
        "decode_access_token",
        return_value=user_id,
    ):
        with pytest.raises(
            HTTPException,
        ) as exc_info:
            get_current_user(
                credentials=(
                    create_credentials()
                ),
                db=db,
            )

    assert (
        exc_info.value.status_code
        == 401
    )


def test_inactive_user_returns_401() -> None:
    user_id = uuid4()

    user = SimpleNamespace(
        id=user_id,
        is_active=False,
    )

    db = MagicMock()
    db.get.return_value = user

    with patch(
        "app.security.current_user."
        "decode_access_token",
        return_value=user_id,
    ):
        with pytest.raises(
            HTTPException,
        ) as exc_info:
            get_current_user(
                credentials=(
                    create_credentials()
                ),
                db=db,
            )

    assert (
        exc_info.value.status_code
        == 401
    )