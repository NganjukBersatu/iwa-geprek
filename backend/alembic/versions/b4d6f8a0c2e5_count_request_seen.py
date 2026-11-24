"""pengajuan tutup periode: kapan dan oleh siapa pertama kali dilihat admin

Revision ID: b4d6f8a0c2e5
Revises: d6f8a0c2e457
Create Date: 2026-11-16 16:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'b4d6f8a0c2e5'
down_revision: Union[str, Sequence[str], None] = 'd6f8a0c2e457'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")

# Kolom baru boleh kosong, jadi baris lama tidak disentuh dan jumlah baris tidak berubah.
COLUMNS = (
    'ALTER TABLE ingredient_count_requests ADD COLUMN IF NOT EXISTS seen_at TIMESTAMPTZ',
    'ALTER TABLE ingredient_count_requests ADD COLUMN IF NOT EXISTS seen_by TEXT',
    'CREATE INDEX IF NOT EXISTS index_ingredient_count_requests_on_seen_by ON ingredient_count_requests (seen_by)',
)

FOREIGN_KEY = """
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_ingredient_count_requests_seen_by_staff') THEN
        ALTER TABLE ingredient_count_requests ADD CONSTRAINT fk_ingredient_count_requests_seen_by_staff FOREIGN KEY (seen_by) REFERENCES staff(id) ON DELETE SET NULL NOT VALID;
    END IF;
END $$;
"""


def upgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    for statement in COLUMNS:
        op.execute(statement)
    op.execute(FOREIGN_KEY)
    op.execute('ALTER TABLE ingredient_count_requests VALIDATE CONSTRAINT fk_ingredient_count_requests_seen_by_staff')


def downgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    op.execute('ALTER TABLE ingredient_count_requests DROP CONSTRAINT IF EXISTS fk_ingredient_count_requests_seen_by_staff')
    op.execute('DROP INDEX IF EXISTS index_ingredient_count_requests_on_seen_by')
    op.execute('ALTER TABLE ingredient_count_requests DROP COLUMN IF EXISTS seen_by')
    op.execute('ALTER TABLE ingredient_count_requests DROP COLUMN IF EXISTS seen_at')
