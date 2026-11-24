"""Satu pintu pagination kursor (keyset): posisi baris terakhir diberikan sebagai token buram bertanda tangan, terikat daftar dan filternya, tanpa memberi hak akses."""
import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime

from app.core.errors import DomainError
from app.core.settings import settings

DEFAULT_LIMIT = 50
MAX_LIMIT = 100
MAX_CURSOR_LENGTH = 512
BAD_REQUEST = 400
INVALID_CURSOR = "Halaman berikutnya tidak lagi berlaku. Muat ulang daftarnya."

# Kunci turunan, supaya tanda tangan kursor tidak pernah bisa dipakai sebagai tanda tangan token masuk.
_KEY = hmac.new(settings.jwt_secret_key.encode(), b"page-cursor", hashlib.sha256).digest()


@dataclass(frozen=True)
class Position:
    at: datetime
    id: str


def _encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _decode(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _signature(scope: str, body: bytes) -> bytes:
    return hmac.new(_KEY, scope.encode() + b"\0" + body, hashlib.sha256).digest()


def encode(scope: str, position: Position) -> str:
    # scope memuat semua yang menentukan isi daftar, misalnya sesi dan kata yang dicari.
    body = json.dumps({"at": position.at.isoformat(), "id": position.id}, separators=(",", ":")).encode()
    return f"{_encode(body)}.{_encode(_signature(scope, body))}"


def decode(scope: str, token: str) -> Position:
    try:
        body_text, signature_text = token.split(".", 1)
        body = _decode(body_text)
        if not hmac.compare_digest(_decode(signature_text), _signature(scope, body)):
            raise ValueError("signature")
        found = json.loads(body)
        position = Position(at=datetime.fromisoformat(found["at"]), id=str(found["id"]))
    except (ValueError, KeyError, TypeError) as error:
        raise DomainError(INVALID_CURSOR, status=BAD_REQUEST) from error
    if position.at.tzinfo is None:
        raise DomainError(INVALID_CURSOR, status=BAD_REQUEST)
    return position
