"""A tablet trades its pairing code for the token it signs in with; the code stays valid so a tablet that left can be paired again without revoking."""
import logging
import secrets
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import as_aware, now
from app.core.devices import codes, print_routing
from app.core.errors import DomainError
from app.core.security import hash_token
from app.models.device import REGISTERED, Device

log = logging.getLogger("cafe.devices")

WAITING = "menunggu"
TOKEN_BYTES = 32
# One sentence for every failure, so a code cannot be guessed from the answers.
INVALID_CODE = "Kode perangkat tidak valid atau sudah kedaluwarsa."


@dataclass(frozen=True)
class Hardware:
    android_id: str | None
    serial: str | None
    brand: str | None
    model: str | None


def redeem(db: Session, code: str, hardware: Hardware) -> tuple[Device, str]:
    """A waiting or registered tablet trades its code for a fresh token, which signs out whatever tablet held the old one; only the token's hash is kept."""
    device = db.scalar(select(Device).where(Device.code_hash == hash_token(codes.normalise(code))).with_for_update())
    # Batas waktu hanya berlaku pada kode lama yang terbit sebelum kode disimpan apa adanya.
    expired = device is not None and device.code_expires_at is not None and as_aware(device.code_expires_at) < now()
    if device is None or device.status not in (WAITING, REGISTERED) or expired:
        raise DomainError(INVALID_CODE)
    if device.status == REGISTERED:
        # Memasang ulang perangkat aktif mengeluarkan perangkat lama yang memegang token sebelumnya, jadi dicatat sebagai kejadian keamanan.
        log.warning("device re-paired: device_id=%s outlet_id=%s", device.id, device.outlet_id, extra={"security": True})
    token = secrets.token_urlsafe(TOKEN_BYTES)
    device.token_hash = hash_token(token)
    device.status = REGISTERED
    if device.pairing_code is None:
        # Kode lama tanpa salinan tetap sekali pakai.
        device.code_hash = None
        device.code_expires_at = None
    device.android_id = hardware.android_id
    device.serial = hardware.serial
    device.brand = hardware.brand
    device.model = hardware.model
    device.paired_at = now()
    # Tablet yang baru terdaftar langsung menyalakan stasiun yang dipegangnya di cabang itu.
    print_routing.sync_used(db, device.outlet_id)
    db.commit()
    return device, token
