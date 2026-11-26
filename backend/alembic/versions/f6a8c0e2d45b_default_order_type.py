"""jenis pesanan bawaan per cabang

Revision ID: f6a8c0e2d45b
Revises: e5f7a9b1c34a
Create Date: 2026-11-26 22:30:00.000000

Kasir memulai setiap pesanan baru dengan jenis ini; nilai awal free_table menjaga perilaku sebelumnya.
Hanya menambah kolom bernilai bawaan konstan dan CHECK yang divalidasi terpisah, jadi tabel tidak ditulis ulang.
"""
from collections.abc import Sequence

from alembic import op

revision: str = 'f6a8c0e2d45b'
down_revision: str | Sequence[str] | None = 'e5f7a9b1c34a'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")
CONSTRAINT = 'check_cafe_settings_default_order_type'

ADD_COLUMN = "ALTER TABLE cafe_settings ADD COLUMN IF NOT EXISTS default_order_type TEXT NOT NULL DEFAULT 'free_table'"

# Dibuat NOT VALID lalu divalidasi terpisah, dan dilewati bila sudah ada supaya migrasi bisa diulang.
ADD_CHECK = f"""
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE connamespace = current_schema()::regnamespace AND conname = '{CONSTRAINT}') THEN
        ALTER TABLE cafe_settings ADD CONSTRAINT {CONSTRAINT} CHECK (default_order_type IN ('free_table', 'take_away')) NOT VALID;
    END IF;
END $$;
"""


def upgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    op.execute(ADD_COLUMN)
    op.execute(ADD_CHECK)
    op.execute(f'ALTER TABLE cafe_settings VALIDATE CONSTRAINT {CONSTRAINT}')


def downgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    op.execute(f'ALTER TABLE cafe_settings DROP CONSTRAINT IF EXISTS {CONSTRAINT}')
    op.execute('ALTER TABLE cafe_settings DROP COLUMN IF EXISTS default_order_type')
