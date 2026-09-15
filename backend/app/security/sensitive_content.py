import re
from pathlib import PurePosixPath


REDACTED_SECRET = "[REDACTED_SECRET]"


SENSITIVE_FILENAMES = {
    ".env",
    ".npmrc",
    ".pypirc",
    ".netrc",
    "id_rsa",
    "id_ed25519",
    "credentials",
}


SAFE_ENV_EXAMPLES = {
    ".env.example",
    ".env.sample",
    ".env.template",
}


SENSITIVE_EXTENSIONS = {
    ".pem",
    ".key",
    ".p12",
    ".pfx",
    ".jks",
    ".keystore",
}


PRIVATE_KEY_PATTERN = re.compile(
    (
        r"-----BEGIN "
        r"[A-Z0-9 ]*PRIVATE KEY-----"
        r".*?"
        r"-----END "
        r"[A-Z0-9 ]*PRIVATE KEY-----"
    ),
    re.IGNORECASE | re.DOTALL,
)


OPENAI_KEY_PATTERN = re.compile(
    r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b",
)


AWS_ACCESS_KEY_PATTERN = re.compile(
    r"\bAKIA[0-9A-Z]{16}\b",
)


GITHUB_CLASSIC_TOKEN_PATTERN = re.compile(
    r"\bghp_[A-Za-z0-9]{20,}\b",
)


GITHUB_FINE_GRAINED_TOKEN_PATTERN = re.compile(
    r"\bgithub_pat_[A-Za-z0-9_]{20,}\b",
)


DATABASE_CREDENTIAL_URL_PATTERN = re.compile(
    (
        r"\b"
        r"(?:"
        r"postgresql(?:\+[A-Za-z0-9_]+)?"
        r"|postgres"
        r"|mysql"
        r"|mongodb(?:\+srv)?"
        r"|redis"
        r")"
        r"://"
        r"[^:\s/@]+"
        r":"
        r"[^@\s/]+"
        r"@"
        r"[^\s\"']+"
    ),
    re.IGNORECASE,
)


SECRET_PATTERNS = (
    PRIVATE_KEY_PATTERN,
    OPENAI_KEY_PATTERN,
    AWS_ACCESS_KEY_PATTERN,
    GITHUB_CLASSIC_TOKEN_PATTERN,
    GITHUB_FINE_GRAINED_TOKEN_PATTERN,
    DATABASE_CREDENTIAL_URL_PATTERN,
)


def is_sensitive_path(
    path: str,
) -> bool:
    normalized_path = (
        path
        .replace("\\", "/")
        .lower()
    )

    file_path = PurePosixPath(
        normalized_path,
    )

    filename = file_path.name

    if filename in SAFE_ENV_EXAMPLES:
        return False

    if (
        filename == ".env"
        or filename.startswith(
            ".env.",
        )
    ):
        return True

    if filename in SENSITIVE_FILENAMES:
        return True

    if (
        file_path.suffix
        in SENSITIVE_EXTENSIONS
    ):
        return True

    return False


def contains_sensitive_content(
    content: str,
) -> bool:
    if not content:
        return False

    return any(
        pattern.search(content)
        is not None
        for pattern in SECRET_PATTERNS
    )


def redact_sensitive_content(
    content: str,
) -> str:
    if not content:
        return content

    redacted_content = content

    for pattern in SECRET_PATTERNS:
        redacted_content = (
            pattern.sub(
                REDACTED_SECRET,
                redacted_content,
            )
        )

    return redacted_content


def should_index_file(
    path: str,
    content: str,
) -> bool:
    if is_sensitive_path(
        path,
    ):
        return False

    if contains_sensitive_content(
        content,
    ):
        return False

    return True