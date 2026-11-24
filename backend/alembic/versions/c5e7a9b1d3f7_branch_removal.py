"""hapus permanen cabang: penanda penghapusan berjalan dan indeks jejak uang per cabang

Revision ID: c5e7a9b1d3f7
Revises: a3c5e7b9d2f6
Create Date: 2026-11-16 18:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'c5e7a9b1d3f7'
down_revision: Union[str, Sequence[str], None] = 'a3c5e7b9d2f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")

# Kolom baru boleh kosong dan indeks baru tidak menyentuh baris, jadi jumlah baris dan uang tidak berubah.
STATEMENTS = (
    'ALTER TABLE outlets ADD COLUMN IF NOT EXISTS removal_started_at TIMESTAMPTZ',
    'CREATE INDEX IF NOT EXISTS index_money_changes_on_outlet_id ON money_changes (outlet_id)',
)


def upgrade() -> None:
    for statement in (*TIMEOUTS, *STATEMENTS):
        op.execute(statement)


def downgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    op.execute('DROP INDEX IF EXISTS index_money_changes_on_outlet_id')
    op.execute('ALTER TABLE outlets DROP COLUMN IF EXISTS removal_started_at')
