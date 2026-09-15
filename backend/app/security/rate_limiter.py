from collections import deque
from dataclasses import dataclass
from threading import Lock
from time import monotonic
from typing import Callable
from fastapi import HTTPException, Request, status


@dataclass(frozen=True)
class RateLimitPolicy:
    requests: int
    window_seconds: int

    def __post_init__(self) -> None:
        if self.requests <= 0:
            raise ValueError(
                "requests debe ser mayor que cero.",
            )

        if self.window_seconds <= 0:
            raise ValueError(
                "window_seconds debe ser mayor que cero.",
            )


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._requests: dict[
            str,
            deque[float],
        ] = {}

        self._lock = Lock()

    def allow(
        self,
        key: str,
        policy: RateLimitPolicy,
        *,
        now: float | None = None,
    ) -> bool:
        current_time = (
            monotonic()
            if now is None
            else now
        )

        cutoff = (
            current_time
            - policy.window_seconds
        )

        with self._lock:
            timestamps = (
                self._requests.setdefault(
                    key,
                    deque(),
                )
            )

            while (
                timestamps
                and timestamps[0] <= cutoff
            ):
                timestamps.popleft()

            if (
                len(timestamps)
                >= policy.requests
            ):
                return False

            timestamps.append(
                current_time,
            )

            return True

    def clear(self) -> None:
        with self._lock:
            self._requests.clear()


RATE_LIMITER = InMemoryRateLimiter()


CHAT_RATE_LIMIT = RateLimitPolicy(
    requests=30,
    window_seconds=60,
)

GENERATION_RATE_LIMIT = RateLimitPolicy(
    requests=10,
    window_seconds=60,
)

UPLOAD_RATE_LIMIT = RateLimitPolicy(
    requests=5,
    window_seconds=60,
)


def build_rate_limit_dependency(
    policy: RateLimitPolicy,
    limiter: InMemoryRateLimiter | None = None,
) -> Callable[[Request], None]:
    selected_limiter = (
        limiter
        if limiter is not None
        else RATE_LIMITER
    )

    def dependency(
        request: Request,
    ) -> None:
        key = _build_rate_limit_key(
            request,
        )

        allowed = selected_limiter.allow(
            key=key,
            policy=policy,
        )

        if allowed:
            return

        raise HTTPException(
            status_code=(
                status.HTTP_429_TOO_MANY_REQUESTS
            ),
            detail=(
                "Demasiadas solicitudes. "
                "Inténtalo de nuevo en unos segundos."
            ),
            headers={
                "Retry-After": str(
                    policy.window_seconds,
                ),
            },
        )

    return dependency


def _build_rate_limit_key(
    request: Request,
) -> str:
    client_host = (
        request.client.host
        if request.client is not None
        else "unknown"
    )

    route = request.scope.get(
        "route",
    )

    route_path = getattr(
        route,
        "path",
        None,
    )

    path = (
        route_path
        if isinstance(route_path, str)
        else request.url.path
    )

    return (
        f"{client_host}:"
        f"{request.method}:"
        f"{path}"
    )


enforce_chat_rate_limit = (
    build_rate_limit_dependency(
        CHAT_RATE_LIMIT,
    )
)

enforce_generation_rate_limit = (
    build_rate_limit_dependency(
        GENERATION_RATE_LIMIT,
    )
)

enforce_upload_rate_limit = (
    build_rate_limit_dependency(
        UPLOAD_RATE_LIMIT,
    )
)