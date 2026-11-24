"""riwayat tugas outlet: indeks hari pengisian untuk daftar lintas cabang

Revision ID: d6f8b0c2e4a9
Revises: b1e3a5c7d879
Create Date: 2026-11-17 14:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'd6f8b0c2e4a9'
down_revision: Union[str, Sequence[str], None] = 'b1e3a5c7d879'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")

# Indeks baru tidak menyentuh baris, jadi jumlah baris dan uang tidak berubah; daftar satu cabang sudah dilayani unique (batch_id, day).
STATEMENTS = ('CREATE INDEX IF NOT EXISTS index_outlet_batch_runs_on_day ON outlet_batch_runs (day)',)


def upgrade() -> None:
    for statement in (*TIMEOUTS, *STATEMENTS):
        op.execute(statement)


def downgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    op.execute('DROP INDEX IF EXISTS index_outlet_batch_runs_on_day')
