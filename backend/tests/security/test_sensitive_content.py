import pytest

from app.security.sensitive_content import (
    contains_sensitive_content,
    is_sensitive_path,
    should_index_file,
)


@pytest.mark.parametrize(
    "path",
    [
        ".env",
        ".env.local",
        ".env.production",
        "backend/.env",
        "frontend/.env.development",
        ".npmrc",
        "backend/.pypirc",
        ".netrc",
        "id_rsa",
        "keys/id_ed25519",
        "certificate.pem",
        "private.key",
        "certificate.p12",
        "certificate.pfx",
        "application.jks",
        "application.keystore",
    ],
)
def test_sensitive_paths_are_blocked(
    path: str,
) -> None:
    assert (
        is_sensitive_path(path)
        is True
    )


@pytest.mark.parametrize(
    "path",
    [
        ".env.example",
        ".env.sample",
        ".env.template",
        "backend/.env.example",
        "src/app/app.ts",
        "package.json",
        "README.md",
    ],
)
def test_safe_paths_are_allowed(
    path: str,
) -> None:
    assert (
        is_sensitive_path(path)
        is False
    )


def test_detects_private_key() -> None:
    content = """
-----BEGIN PRIVATE KEY-----
abc123
-----END PRIVATE KEY-----
"""

    assert (
        contains_sensitive_content(
            content,
        )
        is True
    )


def test_detects_rsa_private_key() -> None:
    content = """
-----BEGIN RSA PRIVATE KEY-----
abc123
-----END RSA PRIVATE KEY-----
"""

    assert (
        contains_sensitive_content(
            content,
        )
        is True
    )


def test_detects_openai_api_key() -> None:
    content = (
        "OPENAI_API_KEY="
        "sk-proj-"
        "abcdefghijklmnopqrstuvwxyz123456"
    )

    assert (
        contains_sensitive_content(
            content,
        )
        is True
    )


def test_detects_aws_access_key() -> None:
    content = (
        "AWS_ACCESS_KEY_ID="
        "AKIAABCDEFGHIJKLMNOP"
    )

    assert (
        contains_sensitive_content(
            content,
        )
        is True
    )


def test_detects_github_token() -> None:
    content = (
        "GITHUB_TOKEN="
        "ghp_abcdefghijklmnopqrstuvwxyz123456"
    )

    assert (
        contains_sensitive_content(
            content,
        )
        is True
    )


def test_normal_source_code_is_safe() -> None:
    content = """
export class AppService {
    getName(): string {
        return 'DevPilot';
    }
}
"""

    assert (
        contains_sensitive_content(
            content,
        )
        is False
    )


def test_should_not_index_env_file() -> None:
    assert (
        should_index_file(
            path=".env",
            content=(
                "DATABASE_URL=postgresql://..."
            ),
        )
        is False
    )


def test_should_not_index_secret_inside_allowed_file() -> None:
    content = (
        "const key = "
        "'sk-proj-"
        "abcdefghijklmnopqrstuvwxyz123456';"
    )

    assert (
        should_index_file(
            path="src/config.ts",
            content=content,
        )
        is False
    )


def test_should_index_normal_source_file() -> None:
    assert (
        should_index_file(
            path="src/app.ts",
            content=(
                "export const app = true;"
            ),
        )
        is True
    )