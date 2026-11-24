"""Hands every page request to the web server that runs beside this one.

Live streams stay open for hours, so they have a pool of their own: a crowd of open screens can never leave the pages without a connection.
"""
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.core.error_answers import web_unavailable
from app.core.request_id import current_request_id
from app.core.settings import settings

log = logging.getLogger(__name__)

API_PREFIXES = ("v2/", "web/management/")
API_EXACT = {"v2", "web/management", "health", "csp-reports", "docs", "redoc", "openapi.json"}
HOP_HEADERS = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade",
    "content-length", "content-encoding", "host",
}
STREAM_MEDIA_TYPE = "text/event-stream"

# A page waits at most this long for a free connection, then is told to try again instead of hanging.
POOL_WAIT_SECONDS = 2.0
CONNECT_SECONDS = 3.0
WRITE_SECONDS = 10.0
PAGE_READ_SECONDS = 30.0
# The server beats every 3 seconds, so ten beats of silence means the stream is dead.
STREAM_READ_SECONDS = 30.0
# Open streams: one per open management screen; the cap is the pool, and the one past it is told to retry.
MAX_PAGE_CONNECTIONS = 64
MAX_STREAM_CONNECTIONS = 200


def _client(max_connections: int, read_seconds: float) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.web_upstream,
        limits=httpx.Limits(max_connections=max_connections, max_keepalive_connections=max_connections // 2),
        timeout=httpx.Timeout(read_seconds, connect=CONNECT_SECONDS, write=WRITE_SECONDS, pool=POOL_WAIT_SECONDS),
    )


_page_client = _client(MAX_PAGE_CONNECTIONS, PAGE_READ_SECONDS)
_stream_client = _client(MAX_STREAM_CONNECTIONS, STREAM_READ_SECONDS)


def _wants_stream(request: Request) -> bool:
    return STREAM_MEDIA_TYPE in request.headers.get("accept", "")


async def _relay(upstream: httpx.Response, request_id: str) -> AsyncIterator[bytes]:
    """Passes the body on as it arrives; a broken stream cannot be answered any more, so it is logged once and ended."""
    try:
        async for chunk in upstream.aiter_raw():
            yield chunk
    except httpx.HTTPError as error:
        log.warning("web stream ended early (%s) request_id=%s", type(error).__name__, request_id)
    finally:
        await upstream.aclose()


async def web_proxy(full_path: str, request: Request):
    if full_path.startswith(API_PREFIXES) or full_path in API_EXACT:
        raise HTTPException(status_code=404)

    stream = _wants_stream(request)
    headers = {k: v for k, v in request.headers.items() if k.lower() not in HOP_HEADERS}
    headers["x-forwarded-host"] = request.headers.get("host", "")
    headers["x-forwarded-proto"] = request.headers.get("x-forwarded-proto", "https")
    headers["accept-encoding"] = "identity"

    client = _stream_client if stream else _page_client
    outgoing = client.build_request(
        request.method,
        "/" + full_path,
        params=request.query_params,
        content=await request.body(),
        headers=headers,
    )
    try:
        upstream = await client.send(outgoing, stream=True)
    except httpx.PoolTimeout:
        log.warning("web pool full (%s) request_id=%s", "stream" if stream else "page", current_request_id())
        return web_unavailable(request)
    except httpx.HTTPError as error:
        log.error("web server unreachable (%s) request_id=%s", type(error).__name__, current_request_id())
        return web_unavailable(request)

    response = StreamingResponse(_relay(upstream, current_request_id()), status_code=upstream.status_code)
    for key, value in upstream.headers.multi_items():
        if key.lower() not in HOP_HEADERS:
            response.headers.append(key, value)
    return response


def install(app: FastAPI) -> None:
    """Adds the catch-all route last, and closes both pools when the application stops."""
    app.add_api_route(
        "/{full_path:path}",
        web_proxy,
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
        include_in_schema=False,
    )
    inner = app.router.lifespan_context

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        async with inner(application):
            yield
        await _page_client.aclose()
        await _stream_client.aclose()

    app.router.lifespan_context = lifespan
