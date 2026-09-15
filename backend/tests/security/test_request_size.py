import json

import pytest

from app.security.request_size import (
    RequestSizeLimitMiddleware,
)


@pytest.mark.anyio
async def test_rejects_streamed_body_without_content_length() -> None:
    endpoint_called = False

    async def app(
        scope,
        receive,
        send,
    ) -> None:
        nonlocal endpoint_called

        while True:
            message = await receive()

            if (
                message["type"]
                != "http.request"
            ):
                continue

            if not message.get(
                "more_body",
                False,
            ):
                break

        endpoint_called = True

        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [],
            },
        )

        await send(
            {
                "type": "http.response.body",
                "body": b"ok",
            },
        )

    middleware = (
        RequestSizeLimitMiddleware(
            app,
            max_bytes=10,
        )
    )

    messages = [
        {
            "type": "http.request",
            "body": b"123456",
            "more_body": True,
        },
        {
            "type": "http.request",
            "body": b"78901",
            "more_body": False,
        },
    ]

    async def receive():
        return messages.pop(0)

    sent_messages = []

    async def send(
        message,
    ) -> None:
        sent_messages.append(
            message,
        )

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/upload",
        "headers": [],
    }

    await middleware(
        scope,
        receive,
        send,
    )

    assert endpoint_called is False

    assert (
        sent_messages[0]["status"]
        == 413
    )

    response_body = json.loads(
        sent_messages[1]["body"],
    )

    assert response_body == {
        "detail": (
            "La peticion supera el tamano maximo permitido."
        ),
    }


@pytest.mark.anyio
async def test_accepts_streamed_body_exactly_at_limit() -> None:
    endpoint_called = False

    async def app(
        scope,
        receive,
        send,
    ) -> None:
        nonlocal endpoint_called

        while True:
            message = await receive()

            if (
                message["type"]
                != "http.request"
            ):
                continue

            if not message.get(
                "more_body",
                False,
            ):
                break

        endpoint_called = True

        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [],
            },
        )

        await send(
            {
                "type": "http.response.body",
                "body": b"ok",
            },
        )

    middleware = (
        RequestSizeLimitMiddleware(
            app,
            max_bytes=10,
        )
    )

    messages = [
        {
            "type": "http.request",
            "body": b"12345",
            "more_body": True,
        },
        {
            "type": "http.request",
            "body": b"67890",
            "more_body": False,
        },
    ]

    async def receive():
        return messages.pop(0)

    sent_messages = []

    async def send(
        message,
    ) -> None:
        sent_messages.append(
            message,
        )

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/upload",
        "headers": [],
    }

    await middleware(
        scope,
        receive,
        send,
    )

    assert endpoint_called is True

    assert (
        sent_messages[0]["status"]
        == 200
    )


@pytest.mark.anyio
async def test_real_body_size_wins_over_false_content_length() -> None:
    endpoint_called = False

    async def app(
        scope,
        receive,
        send,
    ) -> None:
        nonlocal endpoint_called

        while True:
            message = await receive()

            if not message.get(
                "more_body",
                False,
            ):
                break

        endpoint_called = True

        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [],
            },
        )

        await send(
            {
                "type": "http.response.body",
                "body": b"ok",
            },
        )

    middleware = (
        RequestSizeLimitMiddleware(
            app,
            max_bytes=10,
        )
    )

    messages = [
        {
            "type": "http.request",
            "body": b"12345678901",
            "more_body": False,
        },
    ]

    async def receive():
        return messages.pop(0)

    sent_messages = []

    async def send(
        message,
    ) -> None:
        sent_messages.append(
            message,
        )

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/upload",
        "headers": [
            (
                b"content-length",
                b"5",
            ),
        ],
    }

    await middleware(
        scope,
        receive,
        send,
    )

    assert endpoint_called is False

    assert (
        sent_messages[0]["status"]
        == 413
    )