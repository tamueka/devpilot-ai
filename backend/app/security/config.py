import os
from dotenv import load_dotenv


load_dotenv()


DEFAULT_ALLOWED_ORIGINS = (
    "http://localhost:4200",
    "http://127.0.0.1:4200",
)

DEFAULT_TRUSTED_HOSTS = (
    "localhost",
    "127.0.0.1",
    "testserver",
)


def _read_csv_environment(
    variable_name: str,
    default: tuple[str, ...],
) -> list[str]:
    raw_value = os.getenv(
        variable_name,
    )

    if not raw_value:
        return list(
            default,
        )

    values = [
        value.strip()
        for value in raw_value.split(",")
        if value.strip()
    ]

    return (
        values
        if values
        else list(default)
    )


def get_allowed_origins() -> list[str]:
    return _read_csv_environment(
        variable_name="ALLOWED_ORIGINS",
        default=DEFAULT_ALLOWED_ORIGINS,
    )


def get_trusted_hosts() -> list[str]:
    return _read_csv_environment(
        variable_name="TRUSTED_HOSTS",
        default=DEFAULT_TRUSTED_HOSTS,
    )