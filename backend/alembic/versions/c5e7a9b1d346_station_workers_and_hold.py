"""peran yang boleh mengerjakan stasiun per cabang, dan penundaan menu di stasiun (waktu, alasan, dan penunda)

Revision ID: c5e7a9b1d346
Revises: b4d6f8a0c235
Create Date: 2026-11-07 18:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'c5e7a9b1d346'
down_revision: Union[str, Sequence[str], None] = 'b4d6f8a0c235'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")

# Peran jadwal yang boleh mengerjakan satu stasiun di satu cabang; kosong berarti tidak ada karyawan lain yang bisa dipilih.
ROLES_TABLE = """
CREATE TABLE IF NOT EXISTS station_branch_roles (
    outlet_id TEXT NOT NULL,
    station_id TEXT NOT NULL,
    role_id TEXT NOT NULL,
    CONSTRAINT pk_station_branch_roles PRIMARY KEY (outlet_id, station_id, role_id)
)
"""

ROLES_INDEXES = (
    'CREATE INDEX IF NOT EXISTS index_station_branch_roles_on_station_id ON station_branch_roles (station_id)',
    'CREATE INDEX IF NOT EXISTS index_station_branch_roles_on_role_id ON station_branch_roles (role_id)',
)

# Penugasan peran bagian dari pengaturan stasiun di cabang itu, jadi ikut hilang bersama cabang atau stasiunnya; peran yang masih dipakai tidak bisa dihapus.
ROLES_FOREIGN_KEYS = (
    ('station_branch_roles', 'fk_station_branch_roles_outlet_id_outlets', 'outlet_id', 'outlets', 'CASCADE'),
    ('station_branch_roles', 'fk_station_branch_roles_station_id_stations', 'station_id', 'stations', 'CASCADE'),
    ('station_branch_roles', 'fk_station_branch_roles_role_id_roles', 'role_id', 'roles', 'RESTRICT'),
)

# Menu yang ditunda: sampai kapan, alasan yang diketik karyawan, dan siapa yang menunda; ketiganya terisi bersama atau kosong bersama.
HOLD_COLUMNS = (
    'ALTER TABLE station_tasks ADD COLUMN IF NOT EXISTS held_until TIMESTAMPTZ',
    'ALTER TABLE station_tasks ADD COLUMN IF NOT EXISTS hold_reason TEXT',
    'ALTER TABLE station_tasks ADD COLUMN IF NOT EXISTS held_by TEXT',
)

HOLD_CHECKS = (
    ('check_station_tasks_hold_reason_length', 'hold_reason IS NULL OR char_length(hold_reason) BETWEEN 1 AND 100'),
    ('check_station_tasks_hold_together', '(held_until IS NULL) = (hold_reason IS NULL) AND (held_until IS NULL) = (held_by IS NULL)'),
)

HOLD_INDEX = 'CREATE INDEX IF NOT EXISTS index_station_tasks_on_held_by ON station_tasks (held_by) WHERE held_by IS NOT NULL'
HOLD_FOREIGN_KEY = ('station_tasks', 'fk_station_tasks_held_by_staff', 'held_by', 'staff', 'RESTRICT')


def _foreign_key(table: str, name: str, column: str, target: str, action: str) -> str:
    return f"""
    DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE connamespace = current_schema()::regnamespace AND conname = '{name}') THEN
            ALTER TABLE {table} ADD CONSTRAINT {name} FOREIGN KEY ({column}) REFERENCES {target}(id) ON DELETE {action} NOT VALID;
        END IF;
    END $$;
    """


def _check(table: str, name: str, expression: str) -> str:
    return f"""
    DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE connamespace = current_schema()::regnamespace AND conname = '{name}') THEN
            ALTER TABLE {table} ADD CONSTRAINT {name} CHECK ({expression}) NOT VALID;
        END IF;
    END $$;
    """


def upgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    op.execute(ROLES_TABLE)
    for statement in ROLES_INDEXES:
        op.execute(statement)
    for statement in HOLD_COLUMNS:
        op.execute(statement)
    op.execute(HOLD_INDEX)
    for table, name, column, target, action in (*ROLES_FOREIGN_KEYS, HOLD_FOREIGN_KEY):
        op.execute(_foreign_key(table, name, column, target, action))
        op.execute(f'ALTER TABLE {table} VALIDATE CONSTRAINT {name}')
    for name, expression in HOLD_CHECKS:
        op.execute(_check('station_tasks', name, expression))
        op.execute(f'ALTER TABLE station_tasks VALIDATE CONSTRAINT {name}')


def downgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    for name, _expression in HOLD_CHECKS:
        op.execute(f'ALTER TABLE station_tasks DROP CONSTRAINT IF EXISTS {name}')
    op.execute('ALTER TABLE station_tasks DROP CONSTRAINT IF EXISTS fk_station_tasks_held_by_staff')
    op.execute('DROP INDEX IF EXISTS index_station_tasks_on_held_by')
    for column in ('held_by', 'hold_reason', 'held_until'):
        op.execute(f'ALTER TABLE station_tasks DROP COLUMN IF EXISTS {column}')
    op.execute('DROP TABLE IF EXISTS station_branch_roles')
