"""waktu perubahan harga cabang dan metode bayar

Revision ID: e5f7a9b1c34a
Revises: d4e6f8a0b239
Create Date: 2026-11-26 20:45:00.000000

Dipakai halaman perangkat untuk menilai apakah perangkat sudah tersambung sejak data cabang terakhir berubah (seperti Fomo).
Hanya menambah kolom bernilai bawaan; now() stabil per transaksi, jadi PostgreSQL tidak menulis ulang tabel.
"""
from collections.abc import Sequence

from alembic import op

revision: str = 'e5f7a9b1c34a'
down_revision: str | Sequence[str] | None = 'd4e6f8a0b239'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")
TABLES = ('menu_outlet_prices', 'payment_methods')


def upgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    for name in TABLES:
        op.execute(f'ALTER TABLE {name} ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now()')
        # Halaman perangkat membaca waktu perubahan terakhir per cabang; indeks ini membuatnya tetap ringan saat data membesar.
        op.execute(f'CREATE INDEX IF NOT EXISTS ix_{name}_outlet_id_updated_at ON {name} (outlet_id, updated_at)')


def downgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    for name in TABLES:
        op.execute(f'DROP INDEX IF EXISTS ix_{name}_outlet_id_updated_at')
        op.execute(f'ALTER TABLE {name} DROP COLUMN IF EXISTS updated_at')
