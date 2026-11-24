"""trigram search: the pg_trgm extension and a GIN index on every column a person can search, read by app.core.search

Revision ID: d4f6a8c0e215
Revises: c2e4a6b8d103
Create Date: 2026-10-25 17:00:00.000000

If the database refuses the extension, this migration fails inside scripts/pra_deploy.py's transaction and the deploy stops
with nothing changed.
"""
from typing import Sequence, Union

from alembic import op

from app.core.search import trigram_opclass

revision: str = 'd4f6a8c0e215'
down_revision: Union[str, Sequence[str], None] = 'c2e4a6b8d103'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (table, column): every column passed to app.core.search.contains.
SEARCHED = (
    ('shifts', 'catatan'),
    ('shifts', 'kode_shift'),
    ('kategori', 'nama'),
    ('expenses', 'nama_item'),
    ('expenses', 'catatan'),
    ('bahan', 'nama'),
    ('kartu_bahan', 'bahan_nama'),
    ('kartu_bahan', 'catatan'),
    ('menu_items', 'name'),
    ('order_items', 'menu_item_name'),
    ('outlets', 'kode'),
    ('outlets', 'nama'),
    ('roles', 'nama'),
    ('staff', 'name'),
    ('staff', 'username'),
    ('staff', 'no_hp'),
    ('staff', 'email'),
    ('tugas', 'judul'),
    ('tugas', 'keterangan'),
    ('pengajuan_izin', 'alasan'),
)


def index_name(table: str, column: str) -> str:
    return f'ix_trgm_{table}_{column}'


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
    opclass = trigram_opclass(op.get_bind())
    for table, column in SEARCHED:
        op.execute(f'CREATE INDEX IF NOT EXISTS {index_name(table, column)} ON {table} USING gin ({column} {opclass})')


def downgrade() -> None:
    for table, column in SEARCHED:
        op.execute(f'DROP INDEX IF EXISTS {index_name(table, column)}')
