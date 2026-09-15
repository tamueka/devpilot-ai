import pytest

from app.security.sensitive_content import (
    REDACTED_SECRET,
    contains_sensitive_content,
    redact_sensitive_content,
)


def test_redacts_openai_api_key() -> None:
    secret = (
        "sk-proj-"
        "abcdefghijklmnopqrstuvwxyz123456"
    )

    content = (
        f"OPENAI_API_KEY={secret}"
    )

    result = (
        redact_sensitive_content(
            content,
        )
    )

    assert secret not in result

    assert REDACTED_SECRET in result


def test_redacts_aws_access_key() -> None:
    secret = (
        "AKIAABCDEFGHIJKLMNOP"
    )

    result = (
        redact_sensitive_content(
            f"AWS_ACCESS_KEY_ID={secret}",
        )
    )

    assert secret not in result

    assert REDACTED_SECRET in result


def test_redacts_github_classic_token() -> None:
    secret = (
        "ghp_"
        "abcdefghijklmnopqrstuvwxyz123456"
    )

    result = (
        redact_sensitive_content(
            f"GITHUB_TOKEN={secret}",
        )
    )

    assert secret not in result

    assert REDACTED_SECRET in result


def test_redacts_github_fine_grained_token() -> None:
    secret = (
        "github_pat_"
        "abcdefghijklmnopqrstuvwxyz_"
        "1234567890"
    )

    result = (
        redact_sensitive_content(
            f"TOKEN={secret}",
        )
    )

    assert secret not in result

    assert REDACTED_SECRET in result


def test_redacts_entire_private_key() -> None:
    private_key = (
        "-----BEGIN PRIVATE KEY-----\n"
        "SUPER_SECRET_PRIVATE_KEY_DATA\n"
        "ANOTHER_SECRET_LINE\n"
        "-----END PRIVATE KEY-----"
    )

    result = (
        redact_sensitive_content(
            private_key,
        )
    )

    assert (
        "SUPER_SECRET_PRIVATE_KEY_DATA"
        not in result
    )

    assert (
        "ANOTHER_SECRET_LINE"
        not in result
    )

    assert REDACTED_SECRET in result


def test_redacts_rsa_private_key() -> None:
    private_key = (
        "-----BEGIN RSA PRIVATE KEY-----\n"
        "RSA_SECRET_DATA\n"
        "-----END RSA PRIVATE KEY-----"
    )

    result = (
        redact_sensitive_content(
            private_key,
        )
    )

    assert (
        "RSA_SECRET_DATA"
        not in result
    )

    assert REDACTED_SECRET in result


@pytest.mark.parametrize(
    "url",
    [
        (
            "postgresql://"
            "admin:supersecret@localhost:5432/devpilot"
        ),
        (
            "postgresql+psycopg://"
            "admin:supersecret@localhost:5432/devpilot"
        ),
        (
            "mysql://"
            "admin:supersecret@localhost/database"
        ),
        (
            "mongodb://"
            "admin:supersecret@localhost/database"
        ),
        (
            "redis://"
            "admin:supersecret@localhost:6379/0"
        ),
    ],
)
def test_redacts_database_credentials(
    url: str,
) -> None:
    result = (
        redact_sensitive_content(
            f"DATABASE_URL={url}",
        )
    )

    assert url not in result

    assert REDACTED_SECRET in result


def test_preserves_normal_source_code() -> None:
    content = """
export class UserService {
    getToken(): string {
        return response.token;
    }
}
"""

    result = (
        redact_sensitive_content(
            content,
        )
    )

    assert result == content


def test_preserves_normal_password_variable() -> None:
    content = (
        "const password = "
        "form.controls.password.value;"
    )

    assert (
        redact_sensitive_content(
            content,
        )
        == content
    )


def test_multiple_secrets_are_all_redacted() -> None:
    openai_secret = (
        "sk-proj-"
        "abcdefghijklmnopqrstuvwxyz123456"
    )

    aws_secret = (
        "AKIAABCDEFGHIJKLMNOP"
    )

    content = (
        f"OPENAI={openai_secret}\n"
        f"AWS={aws_secret}"
    )

    result = (
        redact_sensitive_content(
            content,
        )
    )

    assert openai_secret not in result
    assert aws_secret not in result

    assert (
        result.count(
            REDACTED_SECRET,
        )
        == 2
    )


def test_redacted_content_is_no_longer_detected_as_sensitive() -> None:
    secret = (
        "sk-proj-"
        "abcdefghijklmnopqrstuvwxyz123456"
    )

    result = (
        redact_sensitive_content(
            secret,
        )
    )

    assert (
        contains_sensitive_content(
            result,
        )
        is False
    )