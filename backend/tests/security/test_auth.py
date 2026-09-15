from uuid import uuid4

import pytest

from app.security.auth import (
    AuthenticationConfigurationError,
    InvalidAccessTokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


@pytest.fixture
def jwt_environment(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        (
            "test-secret-key-"
            "abcdefghijklmnopqrstuvwxyz-"
            "1234567890"
        ),
    )

    monkeypatch.setenv(
        "JWT_ALGORITHM",
        "HS256",
    )

    monkeypatch.setenv(
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
        "60",
    )


def test_password_is_hashed() -> None:
    password = (
        "A-secure-password-123!"
    )

    result = hash_password(
        password,
    )

    assert result != password

    assert (
        password
        not in result
    )


def test_correct_password_is_verified() -> None:
    password = (
        "A-secure-password-123!"
    )

    hashed = hash_password(
        password,
    )

    assert (
        verify_password(
            password,
            hashed,
        )
        is True
    )


def test_wrong_password_is_rejected() -> None:
    hashed = hash_password(
        "correct-password",
    )

    assert (
        verify_password(
            "wrong-password",
            hashed,
        )
        is False
    )


def test_empty_password_cannot_be_hashed() -> None:
    with pytest.raises(
        ValueError,
    ):
        hash_password(
            "",
        )


def test_invalid_hash_returns_false() -> None:
    assert (
        verify_password(
            "password",
            "not-a-valid-hash",
        )
        is False
    )


def test_access_token_round_trip(
    jwt_environment,
) -> None:
    user_id = uuid4()

    token = create_access_token(
        user_id,
    )

    result = decode_access_token(
        token,
    )

    assert result == user_id


def test_token_does_not_expose_secret_key(
    jwt_environment,
    monkeypatch,
) -> None:
    secret = (
        "test-secret-key-"
        "abcdefghijklmnopqrstuvwxyz-"
        "1234567890"
    )

    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        secret,
    )

    token = create_access_token(
        uuid4(),
    )

    assert secret not in token


def test_modified_token_is_rejected(
    jwt_environment,
) -> None:
    token = create_access_token(
        uuid4(),
    )

    header, payload, signature = token.split(
        ".",
    )

    signature_index = len(
        signature,
    ) // 2

    original_character = signature[
        signature_index
    ]

    replacement_character = (
        "A"
        if original_character != "A"
        else "B"
    )

    modified_signature = (
        signature[:signature_index]
        + replacement_character
        + signature[signature_index + 1 :]
    )

    modified_token = ".".join(
        [
            header,
            payload,
            modified_signature,
        ]
    )

    with pytest.raises(
        InvalidAccessTokenError,
    ):
        decode_access_token(
            modified_token,
        )


def test_empty_token_is_rejected(
    jwt_environment,
) -> None:
    with pytest.raises(
        InvalidAccessTokenError,
    ):
        decode_access_token(
            "",
        )


def test_missing_secret_is_rejected(
    monkeypatch,
) -> None:
    monkeypatch.delenv(
        "JWT_SECRET_KEY",
        raising=False,
    )

    with pytest.raises(
        AuthenticationConfigurationError,
    ):
        create_access_token(
            uuid4(),
        )


def test_unsupported_algorithm_is_rejected(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "test-secret",
    )

    monkeypatch.setenv(
        "JWT_ALGORITHM",
        "none",
    )

    with pytest.raises(
        AuthenticationConfigurationError,
    ):
        create_access_token(
            uuid4(),
        )


def test_invalid_expiration_configuration_is_rejected(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "test-secret",
    )

    monkeypatch.setenv(
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
        "invalid",
    )

    with pytest.raises(
        AuthenticationConfigurationError,
    ):
        create_access_token(
            uuid4(),
        )
        