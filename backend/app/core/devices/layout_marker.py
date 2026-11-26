"""Setiap jawaban untuk perangkat yang masuk dengan token perangkat membawa X-Device-Layout, sehingga app membaca tampilannya tanpa permintaan tambahan."""
from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any

from app.core.devices.device_layout import STATE_KEY

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
App = Callable[[Scope, Receive, Send], Awaitable[None]]

HEADER_NAME = b"x-device-layout"


class DeviceLayoutMarker:
    def __init__(self, app: App) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        # Dibuat di sini supaya salinan scope di router tetap memegang dict yang sama dengan yang diisi current_device.
        state = scope.setdefault("state", {})

        async def marked(message: Message) -> None:
            layout = state.get(STATE_KEY)
            if layout is not None and message["type"] == "http.response.start":
                message["headers"] = [*message.get("headers", []), (HEADER_NAME, layout.encode("ascii"))]
            await send(message)

        await self.app(scope, receive, marked)
