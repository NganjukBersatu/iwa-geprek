"""Which tablet a request comes from: the branch of every till call is the branch the tablet was paired to, not the account's."""
from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import current_user
from app.core.database import get_db
from app.core.devices import device_layout, device_stations
from app.core.security import hash_token
from app.models.device import REGISTERED, Device
from app.models.user import User

HEADER = "X-Device"
NOT_PAIRED = "Perangkat ini belum terdaftar. Masukkan kode pasang dari web admin: halaman Cabang, tab Perangkat, buka perangkat ini."
# Penanda yang dibaca app untuk menampilkan layar kode pasang, tanpa mencocokkan teks pesan.
UNPAIRED_HEADERS = {"X-Device-State": "unpaired"}
OTHER_BRANCH = "Akun ini ditempatkan di cabang lain dari perangkat ini."
NOT_CASHIER = "Sesi kas dan transaksi hanya bisa dari perangkat Mode Kasir. Ubah perangkat ini ke Mode Kasir di web admin: halaman Cabang, tab Perangkat."


def tablet(
    request: Request,
    token: str | None = Header(None, alias=HEADER),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> Device:
    device = db.scalar(select(Device).where(Device.token_hash == hash_token(token), Device.status == REGISTERED)) if token else None
    if device is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=NOT_PAIRED, headers=UNPAIRED_HEADERS)
    if user.locked_outlet_id and user.locked_outlet_id != device.outlet_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=OTHER_BRANCH)
    # Permintaan kasir memakai token karyawan, jadi tampilan perangkat ikut ditandai di sini juga, bukan hanya di current_device.
    device_layout.mark(request, device.layout)
    return device


def tablet_outlet_id(device: Device = Depends(tablet)) -> str:
    """The branch every tablet read and write belongs to, for accounts with or without a branch of their own."""
    return device.outlet_id


def cashier_tablet(device: Device = Depends(tablet), db: Session = Depends(get_db)) -> Device:
    if not device_stations.holds_cashier(db, device):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=NOT_CASHIER)
    return device
