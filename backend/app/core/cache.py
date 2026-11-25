"""The one door to the cache: a read route hands over how to compute its answer, and gets it from Redis when nothing it read has changed since.

What a result depends on is not written by hand. While it is computed, every statement is watched and the tables it reads are kept with
the result, next to the version each table had. A commit raises the version of every table it wrote (app.core.live), so a result built
on an older version is never served again; nothing has to list or delete keys. A result whose statements cannot be read for their
tables (a write, a raw function source) is returned but not kept.

Writes never read from here, and when Redis is slow or down every read simply goes to the database.
"""
import hashlib
import json
import logging
import re
import threading
import time
import uuid
from collections.abc import Callable, Iterable
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Protocol, TypeVar

from pydantic import TypeAdapter, ValidationError
from pydantic_core import PydanticSerializationError
from sqlalchemy import event
from sqlalchemy.engine import Engine

from app.core import request_timing
from app.core.demo import state as demo_state
from app.core.cache_store import Store, StoreError
from app.core.clock import today

T = TypeVar("T")
# What a key is made of: the route's own parameters, each a plain value.
Part = str | int | bool | Decimal | date | datetime | Enum | None

# How long a result may live when nothing invalidates it: a safety net, since versions do the real work.
REFERENCE_SECONDS = 3600
LIST_SECONDS = 600
REPORT_SECONDS = 600

PREFIX = "cafe"
VERSION_PREFIX = f"{PREFIX}:ver:"
# Raised by every commit: a result computed while any write landed is not kept, since it may hold either side of it.
SEQUENCE = f"{VERSION_PREFIX}*"
# Every result depends on it; raised when the service starts, because bumps lost in a crash cannot be known.
EPOCH = "@epoch"
LOCK_MILLISECONDS = 3000
WAIT_SECONDS = 0.5
WAIT_STEP_SECONDS = 0.05
# After a failure Redis is left alone this long, so a dead Redis costs one timeout, not one per request.
DOWN_SECONDS = 5
MAX_VALUE_BYTES = 1_000_000

HIT, MISS, SKIP = "hit", "miss", "skip"

log = logging.getLogger("cafe.cache")

_READS = re.compile(r"^\s*(?:SELECT|WITH)\b", re.IGNORECASE)
# The name after FROM or JOIN; a subquery starts with "(" and a column (`IS DISTINCT FROM t.c`) has a dot, so neither is matched.
_SOURCE = re.compile(r'\b(?:FROM|JOIN)\s+"?([A-Za-z_][A-Za-z0-9_]*)\b(?!"?\s*\.)', re.IGNORECASE)


@dataclass
class _Recording:
    tables: set[str] = field(default_factory=set)
    unsafe: str = ""


_recording: ContextVar[_Recording | None] = ContextVar("cache_recording", default=None)


@dataclass
class _Door:
    store: Store | None = None
    build: str = ""
    known: frozenset[str] = frozenset()
    names: re.Pattern[str] | None = None
    unsent: set[str] = field(default_factory=set)
    down_until: float = 0.0
    warned: set[str] = field(default_factory=set)
    lock: threading.Lock = field(default_factory=threading.Lock)


_door = _Door()


def install(engine: Engine) -> None:
    event.listen(engine, "before_cursor_execute", _watch)


def start(store: Store | None, tables: Iterable[str], build: str) -> None:
    """Called once at startup; without a store (no REDIS_URL) every read goes to the database."""
    known = frozenset(tables)
    _door.store = store
    # Each start gets its own space when no deployment id is given, so an old process's results are never read by a new shape.
    _door.build = build or uuid.uuid4().hex
    _door.known = known
    _door.names = re.compile(r"\b(?:" + "|".join(sorted(map(re.escape, known), key=len, reverse=True)) + r")\b") if known else None
    _door.unsent = {EPOCH}
    _door.down_until = 0.0
    _door.warned = set()
    if store is not None:
        _flush()


def tables_changed(tables: Iterable[str]) -> None:
    """Called after every commit, before screens are told: a screen that reloads must not get the old answer."""
    if _door.store is None:
        return
    with _door.lock:
        _door.unsent.update(tables)
    _flush()


def read(name: str, parts: tuple[Part, ...], compute: Callable[[], T], shape: TypeAdapter[T], seconds: int) -> T:
    """`name` is unique per route; `parts` must hold everything the answer depends on: filters, page, branch scope, permission variant."""
    store = _door.store
    # Selama mode demo tidak ada hasil yang disimpan atau dibaca, supaya data demo dan data asli tidak pernah tertukar di cache bersama.
    if store is None or not _usable() or demo_state.is_active():
        request_timing.cache_outcome(SKIP)
        return compute()
    key = _key(name, parts)
    try:
        found = _lookup(store, key, shape)
        if found is not None:
            request_timing.cache_outcome(HIT)
            return found[0]
        if not store.claim(key + ":lock", LOCK_MILLISECONDS):
            found = _wait(store, key, shape)
            if found is not None:
                request_timing.cache_outcome(HIT)
                return found[0]
    except StoreError as error:
        _failed(error)
        request_timing.cache_outcome(SKIP)
        return compute()
    request_timing.cache_outcome(MISS)
    try:
        return _compute_and_keep(store, name, key, compute, shape, seconds)
    finally:
        try:
            store.release(key + ":lock")
        except StoreError as error:
            _failed(error)


class _Role(Protocol):
    permissions: list
    has_full_access: bool


class Viewer(Protocol):
    id: str
    outlet_id: str | None
    role_id: str | None
    role: _Role | None


def viewer(user: Viewer) -> tuple[Part, ...]:
    """The parts of an answer that depends on who asks: the account, its branch, and exactly what its role allows at this moment.

    The permissions are read from the request's own account, so a role the owner changes never keeps serving what it no longer allows.
    """
    role = user.role
    granted = "*" if role is not None and role.has_full_access else ",".join(sorted(role.permissions or [])) if role is not None else ""
    return (user.id, user.outlet_id, user.role_id, hashlib.sha256(granted.encode()).hexdigest()[:16])


def _key(name: str, parts: tuple[Part, ...]) -> str:
    # Today's WIB date is always part of the key: an answer that says "this month" or "now" changes with the day.
    raw = json.dumps([_plain(part) for part in (*parts, today())], separators=(",", ":"))
    return f"{PREFIX}:{_door.build}:{name}:{hashlib.sha256(raw.encode()).hexdigest()[:32]}"


def _plain(part: Part) -> str | int | bool | None:
    if isinstance(part, datetime):
        return part.isoformat()
    if isinstance(part, date):
        # A report bound may carry a clock time, which a plain date string would drop.
        clock = getattr(part, "clock", None)
        return f"{part.isoformat()}T{clock.isoformat()}" if clock is not None else part.isoformat()
    if isinstance(part, Decimal):
        return str(part)
    if isinstance(part, Enum):
        return str(part.value)
    return part


def _lookup(store: Store, key: str, shape: TypeAdapter[T]) -> tuple[T] | None:
    """The kept result, only when every table it read still has the version it was built on."""
    kept = store.get(key)
    if kept is None:
        return None
    header, _, data = kept.partition(b"\n")
    versions: dict[str, str | None] = json.loads(header)
    tables = list(versions)
    current = store.get_many([VERSION_PREFIX + table for table in tables])
    if any(_text(version) != versions[table] for table, version in zip(tables, current)):
        return None
    try:
        return (shape.validate_json(data),)
    except ValidationError as error:
        _warn_once(key, f"a kept result no longer fits its shape: {error.error_count()} errors")
        return None


def _wait(store: Store, key: str, shape: TypeAdapter[T]) -> tuple[T] | None:
    """Another request is computing the same answer: wait a little for it rather than run the same queries again."""
    deadline = time.monotonic() + WAIT_SECONDS
    while time.monotonic() < deadline:
        time.sleep(WAIT_STEP_SECONDS)
        found = _lookup(store, key, shape)
        if found is not None:
            return found
    return None


def _compute_and_keep(store: Store, name: str, key: str, compute: Callable[[], T], shape: TypeAdapter[T], seconds: int) -> T:
    try:
        before = store.get(SEQUENCE)
    except StoreError as error:
        _failed(error)
        return compute()
    recording = _Recording()
    token = _recording.set(recording)
    try:
        value = compute()
    finally:
        _recording.reset(token)
    if recording.unsafe:
        _warn_once(name, recording.unsafe)
        return value
    tables = sorted(recording.tables | {EPOCH})
    try:
        data = shape.dump_json(value)
    except PydanticSerializationError as error:
        _warn_once(name, f"the result does not fit its shape: {error}")
        return value
    if len(data) > MAX_VALUE_BYTES:
        _warn_once(name, f"result of {len(data)} bytes is over {MAX_VALUE_BYTES}")
        return value
    try:
        current = store.get_many([SEQUENCE] + [VERSION_PREFIX + table for table in tables])
        if current[0] != before:
            return value
        header = json.dumps({table: _text(version) for table, version in zip(tables, current[1:])}, separators=(",", ":")).encode()
        store.put(key, header + b"\n" + data, seconds)
    except StoreError as error:
        _failed(error)
    return value


def _watch(_connection: Any, _cursor: Any, statement: str, _parameters: Any, _context: Any, _executemany: bool) -> None:
    recording = _recording.get()
    if recording is None or recording.unsafe:
        return
    if not _READS.match(statement):
        recording.unsafe = "it writes"
        return
    for source in _SOURCE.findall(statement):
        if source not in _door.known:
            recording.unsafe = f"it reads {source}, which is not a known table"
            return
    if _door.names is not None:
        recording.tables.update(_door.names.findall(statement))


def _usable() -> bool:
    return time.monotonic() >= _door.down_until and _flush()


def _flush() -> bool:
    """Sends the version raises that have not reached Redis; until they have, nothing is read from it."""
    store = _door.store
    if store is None:
        return False
    with _door.lock:
        pending = sorted(_door.unsent)
    if not pending:
        return True
    if time.monotonic() < _door.down_until:
        return False
    try:
        store.bump([SEQUENCE] + [VERSION_PREFIX + table for table in pending], time.time_ns())
    except StoreError as error:
        _failed(error)
        return False
    with _door.lock:
        _door.unsent.difference_update(pending)
    return True


def _failed(error: StoreError) -> None:
    _door.down_until = time.monotonic() + DOWN_SECONDS
    log.warning("cache unavailable for %d s, reading from the database: %s", DOWN_SECONDS, error)


def _warn_once(name: str, reason: str) -> None:
    if name not in _door.warned:
        _door.warned.add(name)
        log.warning("%s is not kept in the cache: %s", name, reason)


def _text(version: bytes | None) -> str | None:
    return version.decode() if version is not None else None
