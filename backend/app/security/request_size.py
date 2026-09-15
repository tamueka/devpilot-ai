import json

from starlette.types import (
    ASGIApp,
    Message,
    Receive,
    Scope,
    Send,
)


MAX_REQUEST_SIZE_BYTES = (
    52 * 1024 * 1024
)

REQUEST_TOO_LARGE_DETAIL = (
    "La peticion supera el tamano maximo permitido."
)


class RequestBodyTooLargeError(
    Exception,
):
    pass


class RequestSizeLimitMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        max_bytes: int = MAX_REQUEST_SIZE_BYTES,
    ) -> None:
        if max_bytes <= 0:
            raise ValueError(
                "max_bytes debe ser mayor que cero.",
            )

        self.app = app
        self.max_bytes = max_bytes

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(
                scope,
                receive,
                send,
            )
            return

        content_length = (
            self._get_content_length(
                scope,
            )
        )

        if (
            content_length is not None
            and content_length
            > self.max_bytes
        ):
            await self._send_too_large(
                send,
            )
            return

        received_bytes = 0
        response_started = False

        async def limited_receive() -> Message:
            nonlocal received_bytes

            message = await receive()

            if (
                message["type"]
                == "http.request"
            ):
                body = message.get(
                    "body",
                    b"",
                )

                received_bytes += len(
                    body,
                )

                if (
                    received_bytes
                    > self.max_bytes
                ):
                    raise (
                        RequestBodyTooLargeError
                    )

            return message

        async def tracked_send(
            message: Message,
        ) -> None:
            nonlocal response_started

            if (
                message["type"]
                == "http.response.start"
            ):
                response_started = True

            await send(
                message,
            )

        try:
            await self.app(
                scope,
                limited_receive,
                tracked_send,
            )

        except RequestBodyTooLargeError:
            if response_started:
                raise

            await self._send_too_large(
                send,
            )

    @staticmethod
    def _get_content_length(
        scope: Scope,
    ) -> int | None:
        for name, value in scope.get(
            "headers",
            [],
        ):
            if (
                name.lower()
                != b"content-length"
            ):
                continue

            try:
                content_length = int(
                    value,
                )
            except (
                TypeError,
                ValueError,
            ):
                return None

            if content_length < 0:
                return None

            return content_length

        return None

    @staticmethod
    async def _send_too_large(
        send: Send,
    ) -> None:
        body = json.dumps(
            {
                "detail": (
                    REQUEST_TOO_LARGE_DETAIL
                ),
            },
        ).encode(
            "utf-8",
        )

        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [
                    (
                        b"content-type",
                        b"application/json",
                    ),
                    (
                        b"content-length",
                        str(
                            len(body),
                        ).encode(
                            "ascii",
                        ),
                    ),
                ],
            },
        )

        await send(
            {
                "type": "http.response.body",
                "body": body,
            },
        )