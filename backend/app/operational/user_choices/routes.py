"""Pilihan orang untuk penyaring "Dicatat oleh" di tablet; aturan daftarnya ada di app.core.user_choices.

Tidak di-cache: daftarnya kecil per halaman dan karyawan baru harus langsung bisa dipilih.
"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core import user_choices
from app.core.auth import current_user
from app.core.database import get_db
from app.models.device import Device
from app.models.user import User
from app.operational.device import tablet

router = APIRouter(prefix="/user-choices", tags=["v2-operational-user-choices"])

DEFAULT_SIZE = 30
MAX_SIZE = 100
MAX_SEARCH_LENGTH = 100


class UserChoiceOut(BaseModel):
    id: str
    name: str
    outlet_name: str | None
    is_active: bool


@router.get("", response_model=list[UserChoiceOut])
def list_choices(
    search: str | None = Query(None, max_length=MAX_SEARCH_LENGTH, description="Bagian nama atau nama pengguna"),
    size: int = Query(DEFAULT_SIZE, ge=1, le=MAX_SIZE),
    page: int = Query(1, ge=1, description="Diminta saat daftar digulir; halaman yang lebih pendek dari size adalah akhir"),
    _device: Device = Depends(tablet),
    db: Session = Depends(get_db),
    _user: User = Depends(current_user),
):
    rows = user_choices.page(db, (search or "").strip() or None, size, page)
    return [UserChoiceOut(id=row.id, name=row.name, outlet_name=row.outlet_name, is_active=row.is_active) for row in rows]
