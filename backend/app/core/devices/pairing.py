"""A waiting tablet trades its one-time code for the token it signs in with from then on."""
import secrets
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import as_aware, now
from app.core.devices import codes, print_routing
from app.core.errors import DomainError
from app.core.security import hash_token
from app.models.device import REGISTERED, Device

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
    """The code works once: it is erased as the token is issued, and only the token's hash is kept."""
    device = db.scalar(select(Device).where(Device.code_hash == hash_token(codes.normalise(code))).with_for_update())
    if device is None or device.status != WAITING or device.code_expires_at is None or as_aware(device.code_expires_at) < now():
        raise DomainError(INVALID_CODE)
    token = secrets.token_urlsafe(TOKEN_BYTES)
    device.token_hash = hash_token(token)
    device.status = REGISTERED
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
