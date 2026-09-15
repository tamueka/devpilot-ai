from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.security.security_headers import (
    SecurityHeadersMiddleware,
)


def create_app() -> FastAPI:
    app = FastAPI()

    app.add_middleware(
        SecurityHeadersMiddleware,
    )

    @app.get("/test")
    def test_endpoint() -> dict[str, bool]:
        return {
            "ok": True,
        }

    return app


def test_security_headers_are_present() -> None:
    client = TestClient(
        create_app(),
    )

    response = client.get(
        "/test",
    )

    assert response.status_code == 200

    assert (
        response.headers[
            "x-content-type-options"
        ]
        == "nosniff"
    )

    assert (
        response.headers[
            "x-frame-options"
        ]
        == "DENY"
    )

    assert (
        response.headers[
            "referrer-policy"
        ]
        == "no-referrer"
    )

    assert (
        response.headers[
            "permissions-policy"
        ]
        == (
            "camera=(), "
            "microphone=(), "
            "geolocation=()"
        )
    )

    assert (
        response.headers[
            "cache-control"
        ]
        == "no-store"
    )


def test_security_headers_are_added_to_404_responses() -> None:
    client = TestClient(
        create_app(),
    )

    response = client.get(
        "/does-not-exist",
    )

    assert response.status_code == 404

    assert (
        response.headers[
            "x-content-type-options"
        ]
        == "nosniff"
    )

    assert (
        response.headers[
            "x-frame-options"
        ]
        == "DENY"
    )