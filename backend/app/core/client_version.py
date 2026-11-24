"""Satu pintu pembaruan wajib: aplikasi Android dan PWA di bawah versi minimum ditolak di semua rute /v2, kecuali kasir yang sesinya masih berjalan."""
import json
import logging
import re
from dataclasses import dataclass
from enum import StrEnum

from anyio import to_thread
from sqlalchemy import select

from app.core import messages
from app.core.auth import session_subject
from app.core.database import SessionLocal
from app.core.errors import error_content
from app.core.request_timing import App, Receive, Scope, Send
from app.core.settings import settings
from app.models.cash_session import CashSession, CashSessionStatus

log = logging.getLogger("cafe.client")

UPGRADE_REQUIRED = 426
CLIENT_OUTDATED = "CLIENT_OUTDATED"
CLIENT_HEADER = "x-app-client"
VERSION_HEADER = "x-app-version"
MAX_HEADER_LENGTH = 32
VERSION_PATTERN = re.compile(r"^(\d{1,4})\.(\d{1,4})\.(\d{1,4})$")
# Peramban menyebut dirinya di user agent dan menambah fetch metadata sendiri; aplikasi Android tidak mengirim keduanya.
BROWSER_AGENT_MARK = "Mozilla/"
BROWSER_FETCH_HEADER = "sec-fetch-mode"
V2_PREFIX = "/v2/"
# Masuk, keluar, saluran live, laporan galat, dan rute versi tetap terbuka supaya aplikasi lama bisa keluar dan tahu harus memperbarui.
OPEN_PREFIXES = ("/v2/auth", "/v2/live", "/v2/client-version", "/v2/client-events")
UNCHECKED_METHODS = ("OPTIONS",)

Version = tuple[int, int, int]


class Client(StrEnum):
    APK = "apk"
    PWA = "pwa"
    # Web admin tidak dipasang di perangkat, jadi selalu versi terbaru dan tidak pernah diperiksa.
    WEB = "web"


@dataclass(frozen=True)
class Minimums:
    apk: str | None
    pwa: str | None
    download_url: str | None


def parsed(value: str) -> Version | None:
    found = VERSION_PATTERN.match(value.strip())
    return (int(found[1]), int(found[2]), int(found[3])) if found else None


def _minimum_text(raw: str, name: str) -> str | None:
    """Kosong berarti tidak diperiksa; nilai yang bukan major.minor.patch dicatat dan tidak pernah menahan siapa pun."""
    text = raw.strip()
    if not text:
        return None
    if parsed(text) is None:
        log.error("version check stays off: %s=%r is not major.minor.patch", name, text)
        return None
    return text


def minimums() -> Minimums:
    return Minimums(
        apk=_minimum_text(settings.min_version_apk, "min_version_apk"),
        pwa=_minimum_text(settings.min_version_pwa, "min_version_pwa"),
        download_url=settings.download_url.strip() or None,
    )


def _header(headers: dict[str, str], name: str) -> str:
    return headers.get(name, "")[:MAX_HEADER_LENGTH]


def _client_of(headers: dict[str, str]) -> Client:
    """Aplikasi Android lama tidak mengirim nama, jadi yang bukan peramban dianggap aplikasi Android."""
    named = _header(headers, CLIENT_HEADER).lower()
    if named == Client.APK:
        return Client.APK
    if named == Client.WEB:
        return Client.WEB
    if named == Client.PWA or BROWSER_AGENT_MARK in headers.get("user-agent", "") or BROWSER_FETCH_HEADER in headers:
        return Client.PWA
    return Client.APK


def _outdated(client: Client, version: str, limits: Minimums) -> bool:
    if client == Client.WEB:
        return False
    minimum = limits.apk if client == Client.APK else limits.pwa
    if minimum is None:
        return False
    current = parsed(version)
    # Tanpa versi berarti aplikasi lama yang belum mengirimnya, jadi pasti di bawah minimum.
    return current is None or current < (parsed(minimum) or (0, 0, 0))


def _user_id(headers: dict[str, str]) -> str | None:
    authorization = headers.get("authorization", "")
    if not authorization.lower().startswith("bearer "):
        return None
    return session_subject(authorization[7:].strip())


def _holds_running_session(user_id: str) -> bool:
    with SessionLocal() as db:
        found = db.scalar(select(CashSession.id).where(CashSession.cashier_id == user_id, CashSession.status == CashSessionStatus.OPEN).limit(1))
    return found is not None


async def _allowed(path: str, headers: dict[str, str]) -> bool:
    client = _client_of(headers)
    version = _header(headers, VERSION_HEADER)
    if not _outdated(client, version, minimums()):
        return True
    # Kasir dengan sesi berjalan tetap boleh berjualan sampai sesinya ditutup, supaya uang dan pesanan tidak tertahan.
    user_id = _user_id(headers) if client == Client.APK else None
    grace = user_id is not None and await to_thread.run_sync(_holds_running_session, user_id)
    log.warning("outdated client: client=%s version=%r user=%s grace=%s path=%s", client, version, user_id, grace, path)
    return grace


def _refusal() -> bytes:
    limits = minimums()
    content = error_content(UPGRADE_REQUIRED, messages.CLIENT_OUTDATED, CLIENT_OUTDATED)
    if limits.download_url:
        content["download_url"] = limits.download_url
    return json.dumps(content).encode()


class ClientVersionGate:
    """Menolak dengan 426 setiap permintaan /v2 dari aplikasi di bawah versi minimum, sebelum rute mana pun berjalan."""

    def __init__(self, app: App) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        path = scope.get("path", "")
        checked = scope["type"] == "http" and path.startswith(V2_PREFIX) and not path.startswith(OPEN_PREFIXES) and scope.get("method") not in UNCHECKED_METHODS
        if not checked:
            await self.app(scope, receive, send)
            return
        headers = {key.decode("latin-1").lower(): value.decode("latin-1") for key, value in scope.get("headers", [])}
        if await _allowed(path, headers):
            await self.app(scope, receive, send)
            return
        body = _refusal()
        await send({"type": "http.response.start", "status": UPGRADE_REQUIRED, "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())]})
        await send({"type": "http.response.body", "body": body})
