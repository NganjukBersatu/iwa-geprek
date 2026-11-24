"""How long every request takes and how many statements it ran, per route: logged, and sent back as Server-Timing so the browser shows it.

The numbers are what decides what gets cached and whether a cache helped. Streams are left out, since they stay open by design.
"""
import logging
import time
from collections.abc import Awaitable, Callable, MutableMapping
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any

from app.core.request_id import current_request_id

SLOW_REQUEST_MILLISECONDS = 1000
MILLISECONDS_PER_SECOND = 1000
STREAM_TYPE = b"text/event-stream"
SERVER_ERROR = 500

log = logging.getLogger("cafe.request")

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
App = Callable[[Scope, Receive, Send], Awaitable[None]]


@dataclass
class Tally:
    statements: int = 0
    database_milliseconds: float = 0.0
    # "hit", "miss" or "skip" when the route reads through the cache; empty when it does not.
    cache: str = ""


_current: ContextVar[Tally | None] = ContextVar("request_tally", default=None)


def statement_ran(milliseconds: float) -> None:
    """Called for every statement; outside a request (startup, scripts) it counts nothing."""
    tally = _current.get()
    if tally is not None:
        tally.statements += 1
        tally.database_milliseconds += milliseconds


def cache_outcome(outcome: str) -> None:
    tally = _current.get()
    if tally is not None:
        tally.cache = outcome


def _route_of(scope: Scope) -> str:
    """The full path with each parameter put back as its name, so /user/abc and /user/xyz are one line in the numbers.

    Built from the path, since a route nested in included routers only knows its own part of it.
    """
    names = {str(value): f"{{{name}}}" for name, value in scope.get("path_params", {}).items()}
    return "/".join(names.get(segment, segment) for segment in scope["path"].split("/"))


def _server_timing(tally: Tally, elapsed: float) -> bytes:
    parts = [f"app;dur={elapsed:.0f}", f'db;dur={tally.database_milliseconds:.0f};desc="{tally.statements} query"']
    if tally.cache:
        parts.append(f'cache;desc="{tally.cache}"')
    return ", ".join(parts).encode()


class RequestTiming:
    def __init__(self, app: App) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        tally = Tally()
        token = _current.set(tally)
        started = time.perf_counter()
        status = 0
        streaming = False

        async def timed_send(message: Message) -> None:
            nonlocal status, streaming
            if message["type"] == "http.response.start":
                status = message["status"]
                headers = list(message.get("headers", []))
                streaming = any(name == b"content-type" and value.startswith(STREAM_TYPE) for name, value in headers)
                elapsed = (time.perf_counter() - started) * MILLISECONDS_PER_SECOND
                headers.append((b"server-timing", _server_timing(tally, elapsed)))
                message = {**message, "headers": headers}
            await send(message)

        try:
            await self.app(scope, receive, timed_send)
        except Exception:
            # The error page is written further out, after this one has let go.
            status = status or SERVER_ERROR
            raise
        finally:
            _current.reset(token)
            if not streaming:
                _log(scope, status, tally, (time.perf_counter() - started) * MILLISECONDS_PER_SECOND)


def _log(scope: Scope, status: int, tally: Tally, elapsed: float) -> None:
    level = logging.WARNING if elapsed >= SLOW_REQUEST_MILLISECONDS else logging.INFO
    cache = f", cache {tally.cache}" if tally.cache else ""
    log.log(
        level,
        "%s %s %d, %.0f ms, %d query %.0f ms%s, request %s",
        scope["method"],
        _route_of(scope),
        status,
        elapsed,
        tally.statements,
        tally.database_milliseconds,
        cache,
        current_request_id() or "-",
    )
