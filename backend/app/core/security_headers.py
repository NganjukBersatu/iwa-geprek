"""Security headers on every response, added once here so no route has to remember them.

A route that already set one of these keeps its own value. Streams get them too; "no-store" is right for a stream as well.
"""
from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
App = Callable[[Scope, Receive, Send], Awaitable[None]]

# The API serves data only, so every feature that needs a page (camera, location, payment) stays off.
ALWAYS: tuple[tuple[bytes, bytes], ...] = (
    (b"x-content-type-options", b"nosniff"),
    (b"referrer-policy", b"strict-origin-when-cross-origin"),
    (b"permissions-policy", b"camera=(), microphone=(), geolocation=(), payment=(), usb=()"),
    (b"cross-origin-opener-policy", b"same-origin"),
    (b"cache-control", b"no-store"),
)
HSTS = (b"strict-transport-security", b"max-age=63072000; includeSubDomains")
FORWARDED_PROTOCOL = b"x-forwarded-proto"


def _over_https(scope: Scope) -> bool:
    """Railway ends the TLS and forwards plain http, so the original scheme is read from the header it adds."""
    if scope.get("scheme") == "https":
        return True
    return any(name == FORWARDED_PROTOCOL and value.split(b",")[0].strip() == b"https" for name, value in scope.get("headers", []))


class SecurityHeaders:
    def __init__(self, app: App) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        secure = _over_https(scope)

        async def with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                present = {name.lower() for name, _ in headers}
                wanted = (*ALWAYS, HSTS) if secure else ALWAYS
                headers.extend((name, value) for name, value in wanted if name not in present)
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, with_headers)
