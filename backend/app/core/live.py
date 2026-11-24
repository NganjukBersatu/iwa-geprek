"""The one door through which the server tells open screens that data changed.

Every committed write, from any route, lands here: tables touched in a session are collected on flush and published on commit, so
a screen reloads only what is already saved. What travels is a signal (table names and branches), never data; the screen then
asks the normal, permission-checked routes. There is no polling anywhere: the web listens to /web/management/live, the app to /v2/live.

With REDIS_URL set, every signal travels through one Redis channel that every worker listens to, so any number of workers share
one stream; without it, or while Redis cannot be reached, signals stay inside the worker that made them.
"""
import asyncio
import json
import logging
import signal
import threading
import time
from collections.abc import AsyncIterator, Callable, Iterable
from dataclasses import dataclass, field
from typing import Any

from fastapi.responses import StreamingResponse
from redis import Redis, RedisError
from sqlalchemy import event
from sqlalchemy.orm import ORMExecuteState, Session

from app.core import cache

QUEUE_SIZE = 100
PENDING_KEY = "live_changes"
# A named event, not a comment: the screen can tell "nothing changed" from "the connection died silently",
# and the proxy never sees an idle connection to close.
HEARTBEAT_SECONDS = 3
STREAM_HEADERS = {"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
# What a screen that fell behind receives instead of the signals it could not hold: read everything again.
RESYNC: dict[str, Any] = {"resync": True, "tables": [], "outlets": []}
# Put in every stream's queue when the server is told to stop; a stream that reads it ends.
STOP: dict[str, Any] = {"stop": True, "tables": [], "outlets": []}
# Bookkeeping, not news: a statement run with these options moves no cache version and reloads no screen.
SILENT = {"live_silent": True}
# Kartu yang ditulis juga menggerakkan baris saldo lewat trigger database (migrasi c3e5a7b9d104) yang tidak terlihat sesi, jadi ikut dihitung tersentuh.
TRIGGER_MOVES: dict[str, tuple[str, ...]] = {"ingredient_cards": ("ingredients",), "stock_cards": ("stock_items",)}
CHANNEL = "live:changes"
# Sending waits no longer than a cache read does; listening blocks, and a dead connection is noticed by the health check.
SEND_TIMEOUT_SECONDS = 0.1
HEALTH_CHECK_SECONDS = 10
RECONNECT_SECONDS = 1

log = logging.getLogger(__name__)


class LiveHub:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue] = set()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._closed = False

    def bind(self, loop: asyncio.AbstractEventLoop) -> None:
        """Requests run in a thread pool; the loop is where their signals are queued safely."""
        self._loop = loop

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=QUEUE_SIZE)
        if self._closed:
            queue.put_nowait(STOP)
        self._subscribers.add(queue)
        return queue

    def close(self) -> None:
        """Ends every open stream: the server waits for open connections before it stops, so streams must finish on their own. Runs on the loop."""
        self._closed = True
        for queue in list(self._subscribers):
            self._put(queue, STOP)

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        self._subscribers.discard(queue)

    def publish(self, change: dict[str, Any]) -> None:
        """Through Redis to every worker, this one included; straight to this worker's screens when Redis is absent or unreachable."""
        if relay is not None and relay.send(change):
            return
        self.deliver(change)

    def deliver(self, change: dict[str, Any]) -> None:
        loop = self._loop
        if loop is None:
            return
        for queue in list(self._subscribers):
            loop.call_soon_threadsafe(self._put, queue, change)

    @staticmethod
    def _put(queue: asyncio.Queue, change: dict[str, Any]) -> None:
        try:
            queue.put_nowait(change)
        except asyncio.QueueFull:
            # A slow screen loses the details, never the news: what it could not hold becomes one resync while its connection stays open.
            # The stop signal is never replaced by a resync.
            while not queue.empty():
                queue.get_nowait()
            queue.put_nowait(STOP if change is STOP else RESYNC)


hub = LiveHub()


def close_on_shutdown_signal(loop: asyncio.AbstractEventLoop) -> None:
    """Uvicorn waits for open connections before it runs the lifespan shutdown, so the streams are told to end when the stop signal
    arrives, ahead of uvicorn's own handler, which still runs afterwards. Only the main thread can install handlers."""
    if threading.current_thread() is not threading.main_thread():
        return
    for number in (signal.SIGINT, signal.SIGTERM):
        previous = signal.getsignal(number)

        def handler(received: int, stack: Any, previous: Any = previous) -> None:
            loop.call_soon_threadsafe(hub.close)
            if callable(previous):
                previous(received, stack)

        signal.signal(number, handler)


class Relay:
    """The Redis channel between workers; a listener that lost it tells its screens to read everything again once it is back."""

    def __init__(self, url: str) -> None:
        self._sender = Redis.from_url(url, socket_timeout=SEND_TIMEOUT_SECONDS, socket_connect_timeout=SEND_TIMEOUT_SECONDS)
        self._listener = Redis.from_url(url, socket_connect_timeout=SEND_TIMEOUT_SECONDS, health_check_interval=HEALTH_CHECK_SECONDS)

    def send(self, change: dict[str, Any]) -> bool:
        try:
            self._sender.publish(CHANNEL, json.dumps(change))
            return True
        except RedisError:
            log.warning("live signal kept in this worker: Redis unreachable")
            return False

    def listen(self) -> None:
        missed = False
        while True:
            try:
                with self._listener.pubsub(ignore_subscribe_messages=True) as channel:
                    channel.subscribe(CHANNEL)
                    if missed:
                        hub.deliver(RESYNC)
                        missed = False
                    # get_message, not listen: it wakes every few seconds and runs the health check, so a silently dead connection is found.
                    while True:
                        message = channel.get_message(timeout=HEALTH_CHECK_SECONDS)
                        if message is not None:
                            hub.deliver(json.loads(message["data"]))
            except (RedisError, ValueError):
                log.warning("live channel lost; reconnecting")
                missed = True
                time.sleep(RECONNECT_SECONDS)


relay: Relay | None = None


def start_relay(url: str) -> None:
    """Called once at startup; without a URL the hub stays in this worker."""
    global relay
    if not url or relay is not None:
        return
    relay = Relay(url)
    threading.Thread(target=relay.listen, name="live-relay", daemon=True).start()


@dataclass
class _Pending:
    tables: set[str] = field(default_factory=set)
    outlets: set[str] = field(default_factory=set)
    # A bulk statement names no branch, so its change reaches every screen.
    every_outlet: bool = False


def _pending(session: Session) -> _Pending:
    return session.info.setdefault(PENDING_KEY, _Pending())


def _collect(session: Session, flush_context, instances=None) -> None:
    pending = _pending(session)
    for instance in [*session.new, *session.dirty, *session.deleted]:
        table = getattr(instance, "__tablename__", None)
        if not table:
            continue
        pending.tables.add(table)
        outlet_id = getattr(instance, "outlet_id", None)
        if outlet_id:
            pending.outlets.add(outlet_id)


def _collect_statement(state: ORMExecuteState) -> None:
    """insert(), update() and delete() run without a flush, so they are caught here."""
    if not (state.is_insert or state.is_update or state.is_delete) or state.execution_options.get("live_silent"):
        return
    pending = _pending(state.session)
    pending.tables.add(state.statement.table.name)
    pending.every_outlet = True


def mark(session: Session, tables: Iterable[str]) -> None:
    """SQL mentah lewat text() tidak tertangkap otomatis, jadi tabelnya disebut sendiri sebelum commit."""
    pending = _pending(session)
    pending.tables.update(tables)
    pending.every_outlet = True


def _publish(session: Session) -> None:
    pending: _Pending | None = session.info.pop(PENDING_KEY, None)
    if pending is None or not pending.tables:
        return
    pending.tables.update(moved for table in list(pending.tables) for moved in TRIGGER_MOVES.get(table, ()))
    cache.tables_changed(pending.tables)
    outlets = [] if pending.every_outlet else sorted(pending.outlets)
    hub.publish({"tables": sorted(pending.tables), "outlets": outlets})


def _discard(session: Session, *_: Any) -> None:
    session.info.pop(PENDING_KEY, None)


def watch_commits() -> None:
    """Called at startup; a second call adds nothing."""
    if event.contains(Session, "after_commit", _publish):
        return
    event.listen(Session, "after_flush", _collect)
    event.listen(Session, "do_orm_execute", _collect_statement)
    event.listen(Session, "after_commit", _publish)
    event.listen(Session, "after_rollback", _discard)
    event.listen(Session, "after_soft_rollback", _discard)


def frame(event_name: str, data: dict) -> str:
    return f"event: {event_name}\ndata: {json.dumps(data)}\n\n"


def stream_response(frames: AsyncIterator[str]) -> StreamingResponse:
    return StreamingResponse(frames, media_type="text/event-stream", headers=STREAM_HEADERS)


async def changes(outlet_id: str | None) -> AsyncIterator[str]:
    """Every connection opens with a resync, which is also the catch-up after a dropped one; a branch-bound viewer only hears its branch."""
    queue = hub.subscribe()
    try:
        yield frame("resync", {})
        while True:
            try:
                change = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_SECONDS)
            except asyncio.TimeoutError:
                yield frame("detak", {})
                continue
            if change is STOP:
                return
            if change.get("resync"):
                yield frame("resync", {})
                continue
            if outlet_id and change["outlets"] and outlet_id not in change["outlets"]:
                continue
            yield frame("ubah", change)
    finally:
        hub.unsubscribe(queue)


@dataclass(frozen=True)
class Snapshot:
    event: str
    data: dict
    final: bool
    seconds_left: float


async def record(tables: frozenset[str], read: Callable[[], Snapshot]) -> AsyncIterator[str]:
    """Follows one record: read again only when one of its tables changes or its time runs out, and closed once it is final."""
    queue = hub.subscribe()
    loop = asyncio.get_running_loop()
    try:
        while True:
            snapshot = await asyncio.to_thread(read)
            yield frame(snapshot.event, snapshot.data)
            if snapshot.final:
                return
            deadline = loop.time() + snapshot.seconds_left
            while (left := deadline - loop.time()) > 0:
                try:
                    change = await asyncio.wait_for(queue.get(), timeout=min(HEARTBEAT_SECONDS, left))
                except asyncio.TimeoutError:
                    yield frame("detak", {})
                    continue
                if change is STOP:
                    return
                if change.get("resync") or tables.intersection(change["tables"]):
                    break
    finally:
        hub.unsubscribe(queue)
