"""Versi minimum aplikasi untuk pemeriksaan saat aplikasi dibuka; aturannya di app.core.client_version."""
from fastapi import APIRouter, Response
from pydantic import BaseModel

from app.core import client_version

router = APIRouter(prefix="/client-version", tags=["v2-client-version"])

# Jawaban boleh disimpan sebentar oleh perangkat; nilainya hanya berubah saat pengaturan server diubah.
CACHE_SECONDS = 60


class ClientVersionOut(BaseModel):
    # Kosong berarti versi aplikasi itu tidak diperiksa.
    apk_minimum: str | None
    pwa_minimum: str | None
    download_url: str | None


# Tidak di-cache server: nilainya dibaca dari pengaturan proses, tanpa database.
@router.get("", response_model=ClientVersionOut)
def minimums(response: Response):
    """Terbuka tanpa masuk, supaya aplikasi lama tahu harus memperbarui sebelum apa pun ditolak."""
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    found = client_version.minimums()
    return ClientVersionOut(apk_minimum=found.apk, pwa_minimum=found.pwa, download_url=found.download_url)
