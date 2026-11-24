"""Penyaring "Dicatat oleh" dan rentang hari bisnis untuk daftar catatan yang menyimpan user_id dan business_day; satu pintu untuk semua riwayat tablet."""
from datetime import date

from sqlalchemy import ColumnElement

from app.core.errors import DomainError

RANGE_INCOMPLETE = "Isi tanggal dari dan sampai bersama-sama."
RANGE_REVERSED = "Tanggal dari harus sebelum atau sama dengan tanggal sampai."


def recorded_filters(model, start: date | None, end: date | None, user_id: str | None) -> list[ColumnElement[bool]]:
    """Rentang memakai hari bisnis yang tersimpan, bukan jam catatan, supaya sama dengan laporan; tanpa rentang berarti semua hari."""
    if (start is None) != (end is None):
        raise DomainError(RANGE_INCOMPLETE)
    filters: list[ColumnElement[bool]] = []
    if start is not None and end is not None:
        if start > end:
            raise DomainError(RANGE_REVERSED)
        filters.extend([model.business_day >= start, model.business_day <= end])
    if user_id:
        filters.append(model.user_id == user_id)
    return filters
