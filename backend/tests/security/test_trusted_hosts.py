from fastapi.testclient import TestClient

from app.main import app


client = TestClient(
    app,
)


def test_default_test_host_is_allowed() -> None:
    response = client.get(
        "/projects",
    )

    assert (
        response.status_code
        != 400
    )


def test_localhost_is_allowed() -> None:
    response = client.get(
        "/projects",
        headers={
            "Host": "localhost",
        },
    )

    assert (
        response.status_code
        != 400
    )


def test_ipv4_localhost_is_allowed() -> None:
    response = client.get(
        "/projects",
        headers={
            "Host": "127.0.0.1",
        },
    )

    assert (
        response.status_code
        != 400
    )


def test_unknown_host_is_rejected() -> None:
    response = client.get(
        "/projects",
        headers={
            "Host": "evil.example",
        },
    )

    assert response.status_code == 400

    assert (
        "Invalid host header"
        in response.text
    )