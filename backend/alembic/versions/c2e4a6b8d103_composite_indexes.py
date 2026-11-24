"""composite indexes for the range reads: the branch first, then the date, so one branch's period is read in order without a sort

Revision ID: c2e4a6b8d103
Revises: c5e7a9b1d3f6
Create Date: 2026-10-25 09:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'c2e4a6b8d103'
down_revision: Union[str, Sequence[str], None] = 'c5e7a9b1d3f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (index, table, columns): each serves a read that filters on the branch (or the person) and a date range.
INDEXES = (
    ('ix_orders_outlet_created', 'orders', 'outlet_id, created_at'),
    ('ix_expenses_outlet_created', 'expenses', 'outlet_id, created_at'),
    ('ix_shifts_outlet_start', 'shifts', 'outlet_id, start_time'),
    ('ix_absensi_outlet_tanggal', 'absensi', 'outlet_id, tanggal'),
    ('ix_absensi_staff_tanggal', 'absensi', 'staff_id, tanggal'),
    ('ix_jadwal_shift_outlet_tanggal', 'jadwal_shift', 'outlet_id, tanggal'),
    ('ix_jadwal_shift_kasir_tanggal', 'jadwal_shift', 'kasir_id, tanggal'),
    ('ix_jadwal_libur_outlet_tanggal', 'jadwal_libur', 'outlet_id, tanggal'),
    ('ix_lembur_outlet_tanggal', 'lembur', 'outlet_id, tanggal'),
    ('ix_lembur_staff_tanggal', 'lembur', 'staff_id, tanggal'),
    ('ix_kartu_stok_outlet_menu_created', 'kartu_stok', 'outlet_id, menu_item_id, created_at'),
)


def upgrade() -> None:
    # IF NOT EXISTS: running it twice, or on a database that already has the index, changes nothing.
    for name, table, columns in INDEXES:
        op.execute(f'CREATE INDEX IF NOT EXISTS {name} ON {table} ({columns})')


def downgrade() -> None:
    for name, _table, _columns in INDEXES:
        op.execute(f'DROP INDEX IF EXISTS {name}')
