"""mode tablet: Mode Kasir atau Mode Stasiun per perangkat

Revision ID: a1b3d5f7c902
Revises: f9b1d3e5a720
Create Date: 2026-11-24 22:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'a1b3d5f7c902'
down_revision: Union[str, Sequence[str], None] = 'f9b1d3e5a720'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")

# Bawaan station sama dengan perilaku lama; mode tablet lama diisi di migrasi berikutnya, jadi jumlah baris dan uang tidak berubah.
STATEMENTS = (
    "ALTER TABLE devices ADD COLUMN IF NOT EXISTS mode TEXT NOT NULL DEFAULT 'station'",
    "ALTER TABLE devices DROP CONSTRAINT IF EXISTS check_devices_mode_values",
    "ALTER TABLE devices ADD CONSTRAINT check_devices_mode_values CHECK (mode IN ('cashier', 'station')) NOT VALID",
    "ALTER TABLE devices VALIDATE CONSTRAINT check_devices_mode_values",
)


def upgrade() -> None:
    for statement in (*TIMEOUTS, *STATEMENTS):
        op.execute(statement)


def downgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    op.execute("ALTER TABLE devices DROP CONSTRAINT IF EXISTS check_devices_mode_values")
    op.execute("ALTER TABLE devices DROP COLUMN IF EXISTS mode")
