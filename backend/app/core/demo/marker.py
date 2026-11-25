"""Setiap respons selama mode demo membawa X-Demo-Mode: 1, sehingga web, tablet, dan aplikasi karyawan menampilkan pita demo tanpa permintaan tambahan."""
from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any

from starlette.concurrency import run_in_threadpool

from app.core.demo.state import is_active

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
App = Callable[[Scope, Receive, Send], Awaitable[None]]

HEADER = (b"x-demo-mode", b"1")


class DemoMarker:
    def __init__(self, app: App) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        # Statusnya kadang dibaca dari database, jadi tidak boleh menahan loop permintaan lain.
        active = await run_in_threadpool(is_active)

        async def marked(message: Message) -> None:
            if active and message["type"] == "http.response.start":
                message["headers"] = [*message.get("headers", []), HEADER]
            await send(message)

        await self.app(scope, receive, marked)
