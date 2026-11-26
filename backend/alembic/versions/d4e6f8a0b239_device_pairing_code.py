"""kode pasang perangkat tetap berlaku

Revision ID: d4e6f8a0b239
Revises: c3d5f7a9e128
Create Date: 2026-11-26 20:30:00.000000

Kode pasang disimpan apa adanya supaya admin bisa melihatnya lagi di detail perangkat dan memakainya untuk memasang ulang tanpa Cabut (seperti Fomo).
Hanya menambah kolom dan constraint; kode yang sudah terbit sebelumnya tetap sekali pakai karena salinannya tidak ada.
"""
from collections.abc import Sequence

from alembic import op

revision: str = 'd4e6f8a0b239'
down_revision: str | Sequence[str] | None = 'c3d5f7a9e128'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")
CONSTRAINT = 'check_devices_pairing_code_length'

ADD_COLUMN = 'ALTER TABLE devices ADD COLUMN IF NOT EXISTS pairing_code TEXT'

# Dibuat NOT VALID lalu divalidasi terpisah, dan dilewati bila sudah ada supaya migrasi bisa diulang.
ADD_CHECK = f"""
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE connamespace = current_schema()::regnamespace AND conname = '{CONSTRAINT}') THEN
        ALTER TABLE devices ADD CONSTRAINT {CONSTRAINT} CHECK (pairing_code IS NULL OR char_length(pairing_code) BETWEEN 4 AND 32) NOT VALID;
    END IF;
END $$;
"""

# Kode sekarang berlaku tanpa batas waktu, jadi satu hash hanya boleh milik satu perangkat; tabel perangkat kecil, jadi kuncinya singkat.
UNIQUE_NAME = 'unique_devices_code_hash'
UNIQUE_INDEX = f'CREATE UNIQUE INDEX IF NOT EXISTS {UNIQUE_NAME} ON devices (code_hash) WHERE code_hash IS NOT NULL'


def upgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    op.execute(ADD_COLUMN)
    op.execute(ADD_CHECK)
    op.execute(f'ALTER TABLE devices VALIDATE CONSTRAINT {CONSTRAINT}')
    op.execute(UNIQUE_INDEX)


# Salinan kode hilang; perangkat yang sudah terdaftar tetap jalan karena tokennya tidak berubah.
def downgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    op.execute(f'DROP INDEX IF EXISTS {UNIQUE_NAME}')
    op.execute(f'ALTER TABLE devices DROP CONSTRAINT IF EXISTS {CONSTRAINT}')
    op.execute('ALTER TABLE devices DROP COLUMN IF EXISTS pairing_code')
