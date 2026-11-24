"""indexes for the Laporan Masalah reads: sessions by their close, overpayments by time, ingredient cards per ingredient in order, and orders by promo

Revision ID: b9e1c3d5f702
Revises: a7c9e1b3d528
Create Date: 2026-10-25 20:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'b9e1c3d5f702'
down_revision: Union[str, Sequence[str], None] = 'a7c9e1b3d528'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (index, table, columns): each serves one detector that would otherwise read the whole table.
INDEXES = (
    ('ix_shifts_outlet_end', 'shifts', 'outlet_id, end_time'),
    ('ix_kelebihan_bayar_outlet_waktu', 'kelebihan_bayar', 'outlet_id, waktu'),
    ('ix_kartu_bahan_bahan_created', 'kartu_bahan', 'bahan_id, created_at'),
    ('ix_orders_promo', 'orders', 'promo_diskon_id'),
)


def upgrade() -> None:
    # IF NOT EXISTS: running it twice, or on a database that already has the index, changes nothing.
    for name, table, columns in INDEXES:
        op.execute(f'CREATE INDEX IF NOT EXISTS {name} ON {table} ({columns})')


def downgrade() -> None:
    for name, _table, _columns in INDEXES:
        op.execute(f'DROP INDEX IF EXISTS {name}')
