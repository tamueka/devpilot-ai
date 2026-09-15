from fastapi import (
    Depends,
    FastAPI,
)
from fastapi.testclient import (
    TestClient,
)
from app.security.rate_limiter import (
    InMemoryRateLimiter,
    RateLimitPolicy,
    build_rate_limit_dependency,
)


def test_allows_requests_below_limit() -> None:
    limiter = InMemoryRateLimiter()

    policy = RateLimitPolicy(
        requests=2,
        window_seconds=60,
    )

    assert limiter.allow(
        "client",
        policy,
        now=100,
    )

    assert limiter.allow(
        "client",
        policy,
        now=101,
    )


def test_blocks_requests_above_limit() -> None:
    limiter = InMemoryRateLimiter()

    policy = RateLimitPolicy(
        requests=2,
        window_seconds=60,
    )

    assert limiter.allow(
        "client",
        policy,
        now=100,
    )

    assert limiter.allow(
        "client",
        policy,
        now=101,
    )

    assert not limiter.allow(
        "client",
        policy,
        now=102,
    )


def test_allows_requests_after_window_expires() -> None:
    limiter = InMemoryRateLimiter()

    policy = RateLimitPolicy(
        requests=1,
        window_seconds=60,
    )

    assert limiter.allow(
        "client",
        policy,
        now=100,
    )

    assert not limiter.allow(
        "client",
        policy,
        now=120,
    )

    assert limiter.allow(
        "client",
        policy,
        now=161,
    )


def test_different_clients_have_independent_limits() -> None:
    limiter = InMemoryRateLimiter()

    policy = RateLimitPolicy(
        requests=1,
        window_seconds=60,
    )

    assert limiter.allow(
        "client-a",
        policy,
        now=100,
    )

    assert not limiter.allow(
        "client-a",
        policy,
        now=101,
    )

    assert limiter.allow(
        "client-b",
        policy,
        now=101,
    )


def test_clear_resets_limiter() -> None:
    limiter = InMemoryRateLimiter()

    policy = RateLimitPolicy(
        requests=1,
        window_seconds=60,
    )

    assert limiter.allow(
        "client",
        policy,
        now=100,
    )

    assert not limiter.allow(
        "client",
        policy,
        now=101,
    )

    limiter.clear()

    assert limiter.allow(
        "client",
        policy,
        now=102,
    )


def test_rejects_invalid_policy() -> None:
    try:
        RateLimitPolicy(
            requests=0,
            window_seconds=60,
        )

    except ValueError as exc:
        assert "requests" in str(exc)

    else:
        raise AssertionError(
            "Se esperaba ValueError.",
        )


def test_http_dependency_returns_429() -> None:
    limiter = InMemoryRateLimiter()

    policy = RateLimitPolicy(
        requests=2,
        window_seconds=60,
    )

    dependency = (
        build_rate_limit_dependency(
            policy=policy,
            limiter=limiter,
        )
    )

    app = FastAPI()

    @app.get(
        "/expensive",
        dependencies=[
            Depends(
                dependency,
            ),
        ],
    )
    def expensive() -> dict[str, bool]:
        return {
            "ok": True,
        }

    client = TestClient(
        app,
    )

    first = client.get(
        "/expensive",
    )

    second = client.get(
        "/expensive",
    )

    third = client.get(
        "/expensive",
    )

    assert first.status_code == 200
    assert second.status_code == 200

    assert third.status_code == 429

    assert third.json() == {
        "detail": (
            "Demasiadas solicitudes. "
            "Inténtalo de nuevo en unos segundos."
        ),
    }

    assert (
        third.headers[
            "retry-after"
        ]
        == "60"
    )


def test_dynamic_routes_share_same_rate_limit_bucket() -> None:
    limiter = InMemoryRateLimiter()

    policy = RateLimitPolicy(
        requests=1,
        window_seconds=60,
    )

    dependency = (
        build_rate_limit_dependency(
            policy=policy,
            limiter=limiter,
        )
    )

    app = FastAPI()

    @app.get(
        "/projects/{project_id}/expensive",
        dependencies=[
            Depends(
                dependency,
            ),
        ],
    )
    def expensive(
        project_id: str,
    ) -> dict[str, str]:
        return {
            "project_id": project_id,
        }

    client = TestClient(
        app,
    )

    first = client.get(
        "/projects/project-1/expensive",
    )

    second = client.get(
        "/projects/project-2/expensive",
    )

    assert first.status_code == 200

    assert second.status_code == 429