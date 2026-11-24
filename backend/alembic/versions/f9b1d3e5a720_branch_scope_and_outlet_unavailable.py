"""menu habis per cabang, dan promo, pengumuman, serta grup varian yang bisa milik satu cabang

Revision ID: f9b1d3e5a720
Revises: e7a9c1d3f5b8
Create Date: 2026-11-24 21:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'f9b1d3e5a720'
down_revision: Union[str, Sequence[str], None] = 'e7a9c1d3f5b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")

# Baris ada berarti menu habis di cabang itu saja; menyalakan lagi menghapus barisnya.
TABLE = """
CREATE TABLE IF NOT EXISTS menu_outlet_unavailable (
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    menu_item_id TEXT NOT NULL,
    outlet_id TEXT NOT NULL,
    staff_id TEXT,
    CONSTRAINT pk_menu_outlet_unavailable PRIMARY KEY (menu_item_id, outlet_id)
)
"""

# Kosong berarti berlaku di semua cabang; terisi berarti milik satu cabang itu saja dan hanya cabang itu yang mengubahnya dari tablet.
SCOPED_TABLES = ('promos', 'cafe_promotions', 'variant_groups')

# menu_item_id sudah di depan kunci utama; sisanya menopang foreign key-nya.
INDEXES = (
    'CREATE INDEX IF NOT EXISTS index_menu_outlet_unavailable_on_outlet_id ON menu_outlet_unavailable (outlet_id)',
    'CREATE INDEX IF NOT EXISTS index_menu_outlet_unavailable_on_staff_id ON menu_outlet_unavailable (staff_id)',
    *(f'CREATE INDEX IF NOT EXISTS index_{table}_on_outlet_id ON {table} (outlet_id)' for table in SCOPED_TABLES),
)

# (tabel, nama, kolom, tujuan, aksi); tanda habis ikut hilang bersama menu atau cabangnya, sedangkan milik cabang menahan penghapusan cabang sampai dihapus sengaja oleh proses hapus cabang.
FOREIGN_KEYS = (
    ('menu_outlet_unavailable', 'fk_menu_outlet_unavailable_menu_item_id_menu_items', 'menu_item_id', 'menu_items', 'CASCADE'),
    ('menu_outlet_unavailable', 'fk_menu_outlet_unavailable_outlet_id_outlets', 'outlet_id', 'outlets', 'CASCADE'),
    ('menu_outlet_unavailable', 'fk_menu_outlet_unavailable_staff_id_staff', 'staff_id', 'staff', 'SET NULL'),
    *((table, f'fk_{table}_outlet_id_outlets', 'outlet_id', 'outlets', 'RESTRICT') for table in SCOPED_TABLES),
)

# Nama grup varian unik per lingkup: dua cabang boleh punya grup bernama sama, dan satu lingkup tidak.
GROUP_NAME_INDEX = 'unique_variant_groups_name_and_outlet_id'


def _foreign_key(table: str, name: str, column: str, target: str, action: str) -> str:
    return f"""
    DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '{name}') THEN
            ALTER TABLE {table} ADD CONSTRAINT {name} FOREIGN KEY ({column}) REFERENCES {target}(id) ON DELETE {action} NOT VALID;
        END IF;
    END $$;
    """


def upgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    op.execute(TABLE)
    for table in SCOPED_TABLES:
        op.execute(f'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS outlet_id TEXT')
    for statement in INDEXES:
        op.execute(statement)
    for table, name, column, target, action in FOREIGN_KEYS:
        op.execute(_foreign_key(table, name, column, target, action))
    for table, name, _column, _target, _action in FOREIGN_KEYS:
        op.execute(f'ALTER TABLE {table} VALIDATE CONSTRAINT {name}')
    op.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS {GROUP_NAME_INDEX} ON variant_groups (lower(name), COALESCE(outlet_id, ''))")


# Menurunkan versi membuat tanda habis per cabang dan kepemilikan cabang hilang.
def downgrade() -> None:
    op.execute(f'DROP INDEX IF EXISTS {GROUP_NAME_INDEX}')
    for table in SCOPED_TABLES:
        op.execute(f'ALTER TABLE {table} DROP CONSTRAINT IF EXISTS fk_{table}_outlet_id_outlets')
        op.execute(f'DROP INDEX IF EXISTS index_{table}_on_outlet_id')
        op.execute(f'ALTER TABLE {table} DROP COLUMN IF EXISTS outlet_id')
    op.execute('DROP TABLE IF EXISTS menu_outlet_unavailable')
