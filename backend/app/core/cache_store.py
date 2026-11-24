"""Where cached results and table versions live: Redis; only app.core.cache talks to it.

Every failure is a StoreError, which the cache treats as a miss: Redis being slow or down never stops a request, it only removes the speed-up.
"""
from typing import Protocol

from redis import Redis, RedisError
from redis.backoff import NoBackoff
from redis.retry import Retry

# Over the private network a call takes about a millisecond; past this the database answers instead.
TIMEOUT_SECONDS = 0.1
MAX_CONNECTIONS = 10


class StoreError(Exception):
    pass


class Store(Protocol):
    def get(self, key: str) -> bytes | None: ...

    def get_many(self, keys: list[str]) -> list[bytes | None]: ...

    def put(self, key: str, value: bytes, seconds: int) -> None: ...

    def claim(self, key: str, milliseconds: int) -> bool:
        """Takes the key only when nobody holds it; the lock of the one request that computes a missing result."""
        ...

    def release(self, key: str) -> None: ...

    def bump(self, keys: list[str], start: int) -> None:
        """Raises each version; a version that was lost starts again from `start`, never from 1, so it can never match an old one."""
        ...


class RedisStore:
    def __init__(self, url: str) -> None:
        self._client = Redis.from_url(
            url,
            socket_timeout=TIMEOUT_SECONDS,
            socket_connect_timeout=TIMEOUT_SECONDS,
            # No retry: a second attempt only doubles the wait the database would not have.
            retry=Retry(NoBackoff(), 0),
            max_connections=MAX_CONNECTIONS,
        )

    def get(self, key: str) -> bytes | None:
        try:
            return self._client.get(key)
        except RedisError as error:
            raise StoreError(str(error)) from error

    def get_many(self, keys: list[str]) -> list[bytes | None]:
        if not keys:
            return []
        try:
            return list(self._client.mget(keys))
        except RedisError as error:
            raise StoreError(str(error)) from error

    def put(self, key: str, value: bytes, seconds: int) -> None:
        try:
            self._client.set(key, value, ex=seconds)
        except RedisError as error:
            raise StoreError(str(error)) from error

    def claim(self, key: str, milliseconds: int) -> bool:
        try:
            return bool(self._client.set(key, b"1", nx=True, px=milliseconds))
        except RedisError as error:
            raise StoreError(str(error)) from error

    def release(self, key: str) -> None:
        try:
            self._client.delete(key)
        except RedisError as error:
            raise StoreError(str(error)) from error

    def bump(self, keys: list[str], start: int) -> None:
        try:
            pipe = self._client.pipeline(transaction=False)
            for key in keys:
                pipe.set(key, start, nx=True)
                pipe.incr(key)
            pipe.execute()
        except RedisError as error:
            raise StoreError(str(error)) from error
