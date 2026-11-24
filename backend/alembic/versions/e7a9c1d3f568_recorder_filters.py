"""filter pencatat dan tanggal di tablet: pembuat catatan pesanan, dan indeks hari bisnis untuk riwayat stok per jenis

Revision ID: e7a9c1d3f568
Revises: c5e7a9b1d346
Create Date: 2026-11-14 21:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'e7a9c1d3f568'
down_revision: Union[str, Sequence[str], None] = 'c5e7a9b1d346'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")

# Catatan lama (dan yang dibuat backend lama) tidak tahu pembuatnya, jadi kolom ini boleh kosong.
COLUMN = 'ALTER TABLE categories ADD COLUMN IF NOT EXISTS created_by_id TEXT'

# Riwayat Barang Masuk, Rusak dan RnD, dan Jual-Ulang selalu dibaca per cabang, per jenis, dan per rentang hari bisnis.
INDEXES = (
    'CREATE INDEX IF NOT EXISTS index_categories_on_created_by_id ON categories (created_by_id)',
    'CREATE INDEX IF NOT EXISTS index_ingredient_cards_on_outlet_id_and_kind_and_business_day ON ingredient_cards (outlet_id, kind, business_day)',
    'CREATE INDEX IF NOT EXISTS index_stock_cards_on_outlet_id_and_kind_and_business_day ON stock_cards (outlet_id, kind, business_day)',
)

FOREIGN_KEY = 'fk_categories_created_by_id_staff'


def upgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    op.execute(COLUMN)
    for statement in INDEXES:
        op.execute(statement)
    # Pembuat yang dihapus hanya dikosongkan; catatannya tetap dipakai pesanan.
    op.execute(
        f"""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '{FOREIGN_KEY}') THEN
                ALTER TABLE categories ADD CONSTRAINT {FOREIGN_KEY} FOREIGN KEY (created_by_id) REFERENCES staff(id) ON DELETE SET NULL NOT VALID;
            END IF;
        END $$;
        """
    )
    op.execute(f'ALTER TABLE categories VALIDATE CONSTRAINT {FOREIGN_KEY}')


def downgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    op.execute(f'ALTER TABLE categories DROP CONSTRAINT IF EXISTS {FOREIGN_KEY}')
    op.execute('DROP INDEX IF EXISTS index_stock_cards_on_outlet_id_and_kind_and_business_day')
    op.execute('DROP INDEX IF EXISTS index_ingredient_cards_on_outlet_id_and_kind_and_business_day')
    op.execute('DROP INDEX IF EXISTS index_categories_on_created_by_id')
    op.execute('ALTER TABLE categories DROP COLUMN IF EXISTS created_by_id')
