"""pesanan terbuka (Open Bill): ditulis dulu, dibayar belakangan

Revision ID: a1b3d5f7c904
Revises: a1b3d5f7c903
Create Date: 2026-11-23 21:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'a1b3d5f7c904'
down_revision: Union[str, Sequence[str], None] = 'a1b3d5f7c903'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")

# Pesanan yang sudah diterima dapur tetapi belum dibayar; belum dihitung di laporan dan total sesi sampai dibayar.
COLUMNS = (
    'ALTER TABLE orders ADD COLUMN IF NOT EXISTS is_open BOOLEAN NOT NULL DEFAULT false',
    'ALTER TABLE orders ADD COLUMN IF NOT EXISTS settled_at TIMESTAMPTZ',
    # Naik tiap bill diubah atau dibayar; pembayar membawa versi yang dilihatnya supaya total usang ditolak.
    'ALTER TABLE orders ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1',
    # Kunci acak dari tablet untuk pembayaran bill, supaya kirim ulang tidak membayar dua kali.
    'ALTER TABLE orders ADD COLUMN IF NOT EXISTS settle_key VARCHAR(64)',
)

CHECK_OPEN = 'check_orders_open_has_no_payment'
CHECK_KEY = 'check_orders_settle_key_length'


def _check(name: str, condition: str) -> str:
    return f"""
    DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '{name}') THEN
            ALTER TABLE orders ADD CONSTRAINT {name} CHECK ({condition}) NOT VALID;
        END IF;
    END $$;
    """


# Bill terbuka belum punya metode bayar dan uang diterima, dan tidak boleh sudah berstatus dibayar.
OPEN_CONDITION = 'NOT is_open OR (payment_method IS NULL AND cash_received IS NULL AND settled_at IS NULL)'
KEY_CONDITION = 'settle_key IS NULL OR char_length(settle_key) BETWEEN 8 AND 64'

# Daftar bill terbuka satu sesi dan pemeriksaan tutup sesi; pembacanya menulis kondisi is_open persis.
INDEXES = (
    'CREATE INDEX IF NOT EXISTS index_orders_on_cash_session_id_open ON orders (cash_session_id) WHERE is_open',
    'CREATE UNIQUE INDEX IF NOT EXISTS unique_orders_outlet_id_settle_key ON orders (outlet_id, settle_key) WHERE settle_key IS NOT NULL',
)


def upgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    for statement in COLUMNS:
        op.execute(statement)
    op.execute(_check(CHECK_OPEN, OPEN_CONDITION))
    op.execute(_check(CHECK_KEY, KEY_CONDITION))
    op.execute(f'ALTER TABLE orders VALIDATE CONSTRAINT {CHECK_OPEN}')
    op.execute(f'ALTER TABLE orders VALIDATE CONSTRAINT {CHECK_KEY}')
    for statement in INDEXES:
        op.execute(statement)


# Bill yang masih terbuka saat diturunkan tetap tercatat sebagai pesanan biasa tanpa pembayaran; sebelum itu tutup atau batalkan semuanya.
def downgrade() -> None:
    op.execute('DROP INDEX IF EXISTS unique_orders_outlet_id_settle_key')
    op.execute('DROP INDEX IF EXISTS index_orders_on_cash_session_id_open')
    op.execute(f'ALTER TABLE orders DROP CONSTRAINT IF EXISTS {CHECK_KEY}')
    op.execute(f'ALTER TABLE orders DROP CONSTRAINT IF EXISTS {CHECK_OPEN}')
    for column in ('settle_key', 'version', 'settled_at', 'is_open'):
        op.execute(f'ALTER TABLE orders DROP COLUMN IF EXISTS {column}')
