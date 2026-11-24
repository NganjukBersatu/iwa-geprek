"""pengajuan tutup periode stok opname dari tablet, diputus admin di web

Revision ID: d6f8a0c2e457
Revises: f7b9d1e3a528
Create Date: 2026-11-14 18:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'd6f8a0c2e457'
down_revision: Union[str, Sequence[str], None] = 'f7b9d1e3a528'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")

# Satu baris per pengajuan; yang sudah diputus tetap disimpan sebagai riwayat siapa mengajukan dan siapa memutus.
TABLE = """
CREATE TABLE IF NOT EXISTS ingredient_count_requests (
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    decided_at TIMESTAMPTZ,
    period_start DATE NOT NULL,
    id TEXT NOT NULL,
    outlet_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    note TEXT,
    requested_by TEXT,
    decided_by TEXT,
    count_id TEXT,
    CONSTRAINT pk_ingredient_count_requests PRIMARY KEY (id),
    CONSTRAINT check_ingredient_count_requests_status_enum CHECK (status IN ('pending', 'rejected', 'closed')),
    CONSTRAINT check_ingredient_count_requests_note_length CHECK (note IS NULL OR char_length(note) BETWEEN 1 AND 255),
    CONSTRAINT check_ingredient_count_requests_decided_together CHECK ((status = 'pending') = (decided_at IS NULL))
)
"""

INDEXES = (
    'CREATE INDEX IF NOT EXISTS index_ingredient_count_requests_on_outlet_id_and_created_at ON ingredient_count_requests (outlet_id, created_at DESC)',
    'CREATE INDEX IF NOT EXISTS index_ingredient_count_requests_on_status_and_created_at ON ingredient_count_requests (status, created_at DESC)',
    'CREATE INDEX IF NOT EXISTS index_ingredient_count_requests_on_requested_by ON ingredient_count_requests (requested_by)',
    'CREATE INDEX IF NOT EXISTS index_ingredient_count_requests_on_decided_by ON ingredient_count_requests (decided_by)',
    'CREATE INDEX IF NOT EXISTS index_ingredient_count_requests_on_count_id ON ingredient_count_requests (count_id)',
    # Satu cabang paling banyak punya satu pengajuan yang menunggu; pengajuan ganda dari dua tablet ditolak database.
    "CREATE UNIQUE INDEX IF NOT EXISTS unique_ingredient_count_requests_outlet_id_pending ON ingredient_count_requests (outlet_id) WHERE status = 'pending'",
)

# Riwayat pengajuan tidak ikut terhapus berantai: cabang tidak bisa dihapus selama ada, orang dan opname yang hilang hanya dikosongkan.
FOREIGN_KEYS = (
    ('fk_ingredient_count_requests_outlet_id_outlets', 'outlet_id', 'outlets', 'RESTRICT'),
    ('fk_ingredient_count_requests_requested_by_staff', 'requested_by', 'staff', 'SET NULL'),
    ('fk_ingredient_count_requests_decided_by_staff', 'decided_by', 'staff', 'SET NULL'),
    ('fk_ingredient_count_requests_count_id_ingredient_counts', 'count_id', 'ingredient_counts', 'SET NULL'),
)


def _foreign_key(name: str, column: str, target: str, action: str) -> str:
    return f"""
    DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '{name}') THEN
            ALTER TABLE ingredient_count_requests ADD CONSTRAINT {name} FOREIGN KEY ({column}) REFERENCES {target}(id) ON DELETE {action} NOT VALID;
        END IF;
    END $$;
    """


def upgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    op.execute(TABLE)
    for statement in INDEXES:
        op.execute(statement)
    for name, column, target, action in FOREIGN_KEYS:
        op.execute(_foreign_key(name, column, target, action))
    for name, _column, _target, _action in FOREIGN_KEYS:
        op.execute(f'ALTER TABLE ingredient_count_requests VALIDATE CONSTRAINT {name}')


def downgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    op.execute('DROP TABLE IF EXISTS ingredient_count_requests')
