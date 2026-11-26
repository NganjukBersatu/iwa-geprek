"""tampilan perangkat: Otomatis, HP, atau Tablet

Revision ID: c3d5f7a9e128
Revises: b2c4e6a8d017
Create Date: 2026-11-26 21:00:00.000000

Kosong berarti otomatis: app menebak dari sisi terpendek layarnya. Perangkat lama tetap kosong, jadi tampilannya tidak berubah.
"""
from collections.abc import Sequence

from alembic import op

revision: str = 'c3d5f7a9e128'
down_revision: str | Sequence[str] | None = 'b2c4e6a8d017'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")

STATEMENTS = (
    "ALTER TABLE devices ADD COLUMN IF NOT EXISTS layout TEXT",
    "ALTER TABLE devices DROP CONSTRAINT IF EXISTS check_devices_layout_values",
    "ALTER TABLE devices ADD CONSTRAINT check_devices_layout_values CHECK (layout IS NULL OR layout IN ('phone', 'tablet')) NOT VALID",
    "ALTER TABLE devices VALIDATE CONSTRAINT check_devices_layout_values",
)


def upgrade() -> None:
    for statement in (*TIMEOUTS, *STATEMENTS):
        op.execute(statement)


def downgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    op.execute("ALTER TABLE devices DROP CONSTRAINT IF EXISTS check_devices_layout_values")
    op.execute("ALTER TABLE devices DROP COLUMN IF EXISTS layout")
