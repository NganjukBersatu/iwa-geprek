"""Pengaturan kategori shift yang diisi admin: jenis (kerja atau libur) dan rentang jam mulai; kosong berarti tidak ada pemeriksaan. Down tanpa aksi karena menghapus kolom membuang pengaturan admin.

Revision ID: w8c0t2v4p216
Revises: v7b9s1u3o105
Create Date: 2026-11-13 14:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'w8c0t2v4p216'
down_revision: Union[str, Sequence[str], None] = 'v7b9s1u3o105'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")

COLUMNS = (
    'ALTER TABLE categories ADD COLUMN IF NOT EXISTS shift_kind text',
    'ALTER TABLE categories ADD COLUMN IF NOT EXISTS shift_start_from text',
    'ALTER TABLE categories ADD COLUMN IF NOT EXISTS shift_start_until text',
)

# Nama aturan => isi CHECK; semuanya hanya menyentuh kolom baru yang masih kosong, jadi data lama pasti lolos.
CHECKS = (
    ('check_categories_shift_kind_values', "shift_kind IS NULL OR shift_kind IN ('work', 'off')"),
    ('check_categories_shift_start_from_format', "shift_start_from IS NULL OR shift_start_from ~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'"),
    ('check_categories_shift_start_until_format', "shift_start_until IS NULL OR shift_start_until ~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'"),
    ('check_categories_shift_start_pair', '(shift_start_from IS NULL) = (shift_start_until IS NULL)'),
    ('check_categories_shift_start_work_only', "shift_kind IS DISTINCT FROM 'off' OR shift_start_from IS NULL"),
    (
        'check_categories_shift_columns_kind_only',
        "kind = 'kode_shift' OR (shift_kind IS NULL AND shift_start_from IS NULL AND shift_start_until IS NULL)",
    ),
)


def _add_check(name: str, condition: str) -> str:
    return f"""
    DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '{name}') THEN
            ALTER TABLE categories ADD CONSTRAINT {name} CHECK ({condition}) NOT VALID;
        END IF;
    END $$;
    """


def upgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    for statement in COLUMNS:
        op.execute(statement)
    for name, condition in CHECKS:
        op.execute(_add_check(name, condition))
    for name, _ in CHECKS:
        op.execute(f'ALTER TABLE categories VALIDATE CONSTRAINT {name}')


def downgrade() -> None:
    pass
