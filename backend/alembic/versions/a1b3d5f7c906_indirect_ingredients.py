"""bahan tidak langsung dan kunci idempotensi kartu bahan

Revision ID: a1b3d5f7c906
Revises: a1b3d5f7c905
Create Date: 2026-11-25 14:00:00.000000

Hanya menambah kolom, constraint, dan indeks; tidak ada baris yang diisi ulang.
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'a1b3d5f7c906'
down_revision: Union[str, Sequence[str], None] = 'a1b3d5f7c905'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")

# Bahan yang tidak berkurang lewat resep: keluarnya dicatat manual oleh karyawan.
INDIRECT_COLUMN = 'ALTER TABLE ingredients ADD COLUMN IF NOT EXISTS is_indirect BOOLEAN NOT NULL DEFAULT false'

# Kunci acak dari klien, supaya klik ganda atau kirim ulang tidak mencatat dua kartu.
CLIENT_COLUMN = 'ALTER TABLE ingredient_cards ADD COLUMN IF NOT EXISTS client_id VARCHAR(64)'

CHECK_NAME = 'check_ingredient_cards_client_id_length'
CHECK = f"""
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE connamespace = current_schema()::regnamespace AND conname = '{CHECK_NAME}') THEN
        ALTER TABLE ingredient_cards ADD CONSTRAINT {CHECK_NAME} CHECK (client_id IS NULL OR char_length(client_id) BETWEEN 8 AND 64) NOT VALID;
    END IF;
END $$;
"""

INDEX_NAME = 'unique_ingredient_cards_outlet_id_client_id'
# Satu kunci hanya sekali per cabang; kartu tanpa kunci (semua yang lama) tidak ikut.
UNIQUE_INDEX = f'CREATE UNIQUE INDEX IF NOT EXISTS {INDEX_NAME} ON ingredient_cards (outlet_id, client_id) WHERE client_id IS NOT NULL'


def upgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    op.execute(INDIRECT_COLUMN)
    op.execute(CLIENT_COLUMN)
    op.execute(CHECK)
    op.execute(f'ALTER TABLE ingredient_cards VALIDATE CONSTRAINT {CHECK_NAME}')
    op.execute(UNIQUE_INDEX)


# Kartu yang sudah memakai kunci tetap sah tanpa kolomnya; menurunkan versi hanya melepas kunci idempotensi.
def downgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    op.execute(f'DROP INDEX IF EXISTS {INDEX_NAME}')
    op.execute(f'ALTER TABLE ingredient_cards DROP CONSTRAINT IF EXISTS {CHECK_NAME}')
    op.execute('ALTER TABLE ingredient_cards DROP COLUMN IF EXISTS client_id')
    op.execute('ALTER TABLE ingredients DROP COLUMN IF EXISTS is_indirect')
