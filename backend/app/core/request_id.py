"""One ID per request: sent back in the X-Request-ID header and in every error body, and written to the log, so a report can be traced."""
import re
import uuid
from collections.abc import Awaitable, Callable, MutableMapping
from contextvars import ContextVar
from typing import Any

HEADER = b"x-request-id"
# A caller's own ID is kept only when it is short and plain, so it can never carry markup or a line break into a log.
VALID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
App = Callable[[Scope, Receive, Send], Awaitable[None]]

_current: ContextVar[str] = ContextVar("request_id", default="")


def current_request_id() -> str:
    """The ID of the request being served; empty outside a request (startup, scripts)."""
    return _current.get()


class RequestId:
    def __init__(self, app: App) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        sent = next((value.decode("latin-1") for name, value in scope.get("headers", []) if name == HEADER), "")
        request_id = sent if VALID.match(sent) else uuid.uuid4().hex
        token = _current.set(request_id)
        # The answer for an unexpected failure is written outside this middleware, where the variable is gone, so the ID is also kept on the request.
        scope.setdefault("state", {})["request_id"] = request_id

        async def with_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = [(name, value) for name, value in message.get("headers", []) if name.lower() != HEADER]
                headers.append((HEADER, request_id.encode("latin-1")))
                message = {**message, "headers": headers}
            await send(message)

        try:
            await self.app(scope, receive, with_id)
        finally:
            _current.reset(token)
