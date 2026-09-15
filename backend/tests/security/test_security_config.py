from app.security.config import (
    DEFAULT_ALLOWED_ORIGINS,
    DEFAULT_TRUSTED_HOSTS,
    get_allowed_origins,
    get_trusted_hosts,
)


def test_default_allowed_origins(
    monkeypatch,
) -> None:
    monkeypatch.delenv(
        "ALLOWED_ORIGINS",
        raising=False,
    )

    assert get_allowed_origins() == list(
        DEFAULT_ALLOWED_ORIGINS,
    )


def test_allowed_origins_from_environment(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "ALLOWED_ORIGINS",
        (
            "https://devpilot.example.com,"
            "https://admin.example.com"
        ),
    )

    assert get_allowed_origins() == [
        "https://devpilot.example.com",
        "https://admin.example.com",
    ]


def test_allowed_origins_remove_whitespace(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "ALLOWED_ORIGINS",
        (
            " https://one.example.com , "
            " https://two.example.com "
        ),
    )

    assert get_allowed_origins() == [
        "https://one.example.com",
        "https://two.example.com",
    ]


def test_default_trusted_hosts(
    monkeypatch,
) -> None:
    monkeypatch.delenv(
        "TRUSTED_HOSTS",
        raising=False,
    )

    assert get_trusted_hosts() == list(
        DEFAULT_TRUSTED_HOSTS,
    )


def test_trusted_hosts_from_environment(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "TRUSTED_HOSTS",
        (
            "api.devpilot.example.com,"
            "devpilot.example.com"
        ),
    )

    assert get_trusted_hosts() == [
        "api.devpilot.example.com",
        "devpilot.example.com",
    ]