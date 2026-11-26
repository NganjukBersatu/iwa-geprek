"""stasiun Kasir selalu ada

Revision ID: b2c4e6a8d017
Revises: a1b3d5f7c906
Create Date: 2026-11-26 19:00:00.000000

Instalasi baru tidak punya stasiun sama sekali, padahal Mode Kasir memegang stasiun berjenis serah terima; tanpanya perangkat kasir tidak bisa didaftarkan.
Hanya menambah satu baris bila belum ada stasiun serah terima; data yang sudah punya stasiun Kasir tidak berubah.
"""
from collections.abc import Sequence

from alembic import op

revision: str = 'b2c4e6a8d017'
down_revision: str | Sequence[str] | None = 'a1b3d5f7c906'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")

# Nama "Kasir" dipakai bila belum diambil stasiun lain (nama unik tanpa membedakan huruf besar kecil).
ENSURE_CASHIER = """
INSERT INTO stations (name, kind, position)
SELECT
    CASE WHEN EXISTS (SELECT 1 FROM stations WHERE lower(name) = 'kasir') THEN 'Kasir Utama' ELSE 'Kasir' END,
    'handover',
    COALESCE((SELECT max(position) FROM stations), 0) + 1
WHERE NOT EXISTS (SELECT 1 FROM stations WHERE kind = 'handover')
"""


def upgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    op.execute(ENSURE_CASHIER)


# Stasiun Kasir mungkin sudah dipegang perangkat atau tercatat di riwayat, jadi menurunkan versi tidak menghapusnya.
def downgrade() -> None:
    pass
