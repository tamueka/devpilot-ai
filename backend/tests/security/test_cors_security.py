from fastapi.testclient import TestClient
from app.main import app


client = TestClient(
    app,
)


def test_allowed_frontend_origin() -> None:
    response = client.options(
        "/projects",
        headers={
            "Origin":
                "http://localhost:4200",
            "Access-Control-Request-Method":
                "GET",
        },
    )

    assert response.status_code == 200

    assert (
        response.headers[
            "access-control-allow-origin"
        ]
        == "http://localhost:4200"
    )


def test_second_allowed_frontend_origin() -> None:
    response = client.options(
        "/projects",
        headers={
            "Origin":
                "http://127.0.0.1:4200",
            "Access-Control-Request-Method":
                "GET",
        },
    )

    assert response.status_code == 200

    assert (
        response.headers[
            "access-control-allow-origin"
        ]
        == "http://127.0.0.1:4200"
    )


def test_unknown_origin_is_not_allowed() -> None:
    response = client.options(
        "/projects",
        headers={
            "Origin":
                "https://evil.example",
            "Access-Control-Request-Method":
                "GET",
        },
    )

    assert (
        response.headers.get(
            "access-control-allow-origin",
        )
        is None
    )


def test_unsupported_method_is_rejected_by_cors() -> None:
    response = client.options(
        "/projects",
        headers={
            "Origin":
                "http://localhost:4200",
            "Access-Control-Request-Method":
                "TRACE",
        },
    )

    assert response.status_code == 400
    
def test_delete_method_is_allowed_by_cors() -> None:
    response = client.options(
        "/projects/test-project-id",
        headers={
            "Origin":
                "http://localhost:4200",
            "Access-Control-Request-Method":
                "DELETE",
        },
    )

    assert response.status_code == 200

    assert (
        "DELETE"
        in response.headers[
            "access-control-allow-methods"
        ]
    )
    
    
def test_authorization_header_is_allowed() -> None:
    client = TestClient(app)

    response = client.options(
        "/projects",
        headers={
            "Origin": (
                "http://localhost:4200"
            ),
            "Access-Control-Request-Method": (
                "GET"
            ),
            "Access-Control-Request-Headers": (
                "Authorization"
            ),
        },
    )

    assert response.status_code == 200

    allowed_headers = response.headers.get(
        "access-control-allow-headers",
        "",
    ).lower()

    assert (
        "authorization"
        in allowed_headers
    )
    
def test_authorization_and_content_type_headers_are_allowed() -> None:
    client = TestClient(app)

    response = client.options(
        "/chat",
        headers={
            "Origin": "http://localhost:4200",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": (
                "Authorization, Content-Type"
            ),
        },
    )

    assert response.status_code == 200

    allowed_headers = response.headers.get(
        "access-control-allow-headers",
        "",
    ).lower()

    assert "authorization" in allowed_headers
    assert "content-type" in allowed_headers