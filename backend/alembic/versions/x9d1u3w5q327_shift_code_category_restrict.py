"""Kode shift tidak lagi kehilangan kategori diam-diam: foreign key kategori diganti RESTRICT, dengan yang baru dibuat lebih dulu sebelum yang lama dihapus. Down tanpa aksi karena SET NULL lama bisa membuat kode kehilangan kategori.

Revision ID: x9d1u3w5q327
Revises: w8c0t2v4p216
Create Date: 2026-11-13 16:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'x9d1u3w5q327'
down_revision: Union[str, Sequence[str], None] = 'w8c0t2v4p216'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")

# Nama lama diganti nama saat kolom dan tabel berganti nama, jadi FK lama dicari lewat apa yang dirujuknya.
ADD_RESTRICT = """
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE connamespace = current_schema()::regnamespace AND conname = 'fk_shift_codes_category_id_categories') THEN
        ALTER TABLE shift_codes ADD CONSTRAINT fk_shift_codes_category_id_categories
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT NOT VALID;
    END IF;
END $$;
"""

VALIDATE = 'ALTER TABLE shift_codes VALIDATE CONSTRAINT fk_shift_codes_category_id_categories'

DROP_OLD = """
DO $$
DECLARE found record;
BEGIN
    FOR found IN
        SELECT c.conname
        FROM pg_constraint c
        WHERE c.conrelid = 'shift_codes'::regclass
          AND c.contype = 'f'
          AND c.confrelid = 'categories'::regclass
          AND c.conname <> 'fk_shift_codes_category_id_categories'
    LOOP
        EXECUTE format('ALTER TABLE shift_codes DROP CONSTRAINT %I', found.conname);
    END LOOP;
END $$;
"""


def upgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    op.execute(ADD_RESTRICT)
    op.execute(VALIDATE)
    op.execute(DROP_OLD)


def downgrade() -> None:
    pass
