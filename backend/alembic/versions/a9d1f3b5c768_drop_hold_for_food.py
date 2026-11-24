"""stasiun tidak lagi punya penahan makanan: kolom hold_for_food dihapus karena digantikan penundaan menu (held_until, hold_reason, held_by)

Revision ID: a9d1f3b5c768
Revises: b4d6f8a0c2e5
Create Date: 2026-11-18 09:00:00.000000

Tidak ada kode yang membaca kolom ini lagi, dan sistem ini belum pernah dipakai di produksi. Down menambahkannya kembali dengan bentuk semula.
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'a9d1f3b5c768'
down_revision: Union[str, Sequence[str], None] = 'b4d6f8a0c2e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")


def upgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    op.execute('ALTER TABLE stations DROP COLUMN IF EXISTS hold_for_food')
    op.execute('ALTER TABLE station_branch_settings DROP COLUMN IF EXISTS hold_for_food')


def downgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    op.execute('ALTER TABLE stations ADD COLUMN IF NOT EXISTS hold_for_food BOOLEAN NOT NULL DEFAULT false')
    op.execute('ALTER TABLE station_branch_settings ADD COLUMN IF NOT EXISTS hold_for_food BOOLEAN')
