"""harga pokok tetap per menu (tanpa resep) dengan penimpaan per cabang

Revision ID: f7b9d1e3a528
Revises: c5e7a9b1d3f7
Create Date: 2026-11-02 18:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'f7b9d1e3a528'
down_revision: Union[str, Sequence[str], None] = 'c5e7a9b1d3f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")

# Kosong berarti menu memakai resep atau stok terlacak; terisi berarti tanpa resep dengan harga pokok segitu, nol sah.
COLUMN = 'ALTER TABLE menu_items ADD COLUMN IF NOT EXISTS fixed_cost NUMERIC(12, 2)'

TABLE = """
CREATE TABLE IF NOT EXISTS menu_outlet_costs (
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    menu_item_id TEXT NOT NULL,
    outlet_id TEXT NOT NULL,
    cost NUMERIC(12, 2) NOT NULL,
    CONSTRAINT pk_menu_outlet_costs PRIMARY KEY (menu_item_id, outlet_id)
)
"""

# Indeks kolom outlet_id menopang foreign key-nya; menu_item_id sudah di depan kunci utama.
INDEXES = (
    'CREATE INDEX IF NOT EXISTS index_menu_outlet_costs_on_outlet_id ON menu_outlet_costs (outlet_id)',
)

# (tabel, nama, kondisi); dibuat NOT VALID lalu divalidasi terpisah.
CHECKS = (
    ('menu_items', 'check_menu_items_fixed_cost_range', 'fixed_cost IS NULL OR (fixed_cost >= 0 AND fixed_cost < 100000000)'),
    ('menu_outlet_costs', 'check_menu_outlet_costs_cost_range', 'cost >= 0 AND cost < 100000000'),
)

# (tabel, nama, kolom, tujuan, aksi); penimpaan adalah bagian dari menunya dan dari cabangnya.
FOREIGN_KEYS = (
    ('menu_outlet_costs', 'fk_menu_outlet_costs_menu_item_id_menu_items', 'menu_item_id', 'menu_items', 'CASCADE'),
    ('menu_outlet_costs', 'fk_menu_outlet_costs_outlet_id_outlets', 'outlet_id', 'outlets', 'CASCADE'),
)


def _check(table: str, name: str, condition: str) -> str:
    return f"""
    DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE connamespace = current_schema()::regnamespace AND conname = '{name}') THEN
            ALTER TABLE {table} ADD CONSTRAINT {name} CHECK ({condition}) NOT VALID;
        END IF;
    END $$;
    """


def _foreign_key(table: str, name: str, column: str, target: str, action: str) -> str:
    return f"""
    DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE connamespace = current_schema()::regnamespace AND conname = '{name}') THEN
            ALTER TABLE {table} ADD CONSTRAINT {name} FOREIGN KEY ({column}) REFERENCES {target}(id) ON DELETE {action} NOT VALID;
        END IF;
    END $$;
    """


def upgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    op.execute(COLUMN)
    op.execute(TABLE)
    for statement in INDEXES:
        op.execute(statement)
    for table, name, condition in CHECKS:
        op.execute(_check(table, name, condition))
    for table, name, column, target, action in FOREIGN_KEYS:
        op.execute(_foreign_key(table, name, column, target, action))
    for table, name, _condition in CHECKS:
        op.execute(f'ALTER TABLE {table} VALIDATE CONSTRAINT {name}')
    for table, name, _column, _target, _action in FOREIGN_KEYS:
        op.execute(f'ALTER TABLE {table} VALIDATE CONSTRAINT {name}')


# Pesanan lama menyimpan unit_cost sendiri, jadi menurunkan versi tidak mengubah riwayat laba.
def downgrade() -> None:
    op.execute('DROP TABLE IF EXISTS menu_outlet_costs')
    op.execute('ALTER TABLE menu_items DROP CONSTRAINT IF EXISTS check_menu_items_fixed_cost_range')
    op.execute('ALTER TABLE menu_items DROP COLUMN IF EXISTS fixed_cost')
