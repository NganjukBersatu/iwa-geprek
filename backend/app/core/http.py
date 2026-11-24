"""Satu pintu alamat berkas: semua alamat foto dan media dibentuk dari PUBLIC_URL layanan v2 ini."""
import re

from app.core.settings import settings

STATIC_PATH = "static"
SOP_FOLDER = "sop"
SOP_MEDIA_ROUTE = "/v2/sop/media"
_FILE_NAME = r"[0-9a-f-]{36}\.[A-Za-z0-9]+"
# Data lama dari backend lama bisa menyimpan alamat penuh, dengan host apa pun, alih-alih path berkas.
_LEGACY_STATIC = re.compile(rf"^(?:https?://[^/\s]+)?/{STATIC_PATH}/(.+)$", re.IGNORECASE)
_SOP_MEDIA = re.compile(rf"(?:https?://[^/\s\"'<>]+)?(?:/{STATIC_PATH}/{SOP_FOLDER}|{SOP_MEDIA_ROUTE})/({_FILE_NAME})")


def public_base_url() -> str:
    return settings.public_url


def stored_path(value: str | None) -> str | None:
    """Path berkas dari isi kolom, termasuk alamat penuh lama; None bila kosong."""
    if not value:
        return None
    legacy = _LEGACY_STATIC.match(value)
    return legacy.group(1) if legacy else value


def static_url(base_url: str, path: str | None) -> str | None:
    """The public address of a stored file, or None when there is no file."""
    stored = stored_path(path)
    return f"{base_url}/{STATIC_PATH}/{stored}" if stored else None


def sop_media_url(base_url: str, name: str) -> str:
    return f"{base_url}{SOP_MEDIA_ROUTE}/{name}"


def sop_media_names(body: str) -> list[str]:
    return _SOP_MEDIA.findall(body)


def with_current_sop_media(body: str, base_url: str) -> str:
    """Isi slide dengan setiap media SOP, bentuk lama atau host lain, menunjuk ke alamat v2 saat ini."""
    return _SOP_MEDIA.sub(lambda match: sop_media_url(base_url, match.group(1)), body)
