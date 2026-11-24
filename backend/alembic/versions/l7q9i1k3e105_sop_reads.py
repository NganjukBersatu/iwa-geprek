"""sop reads: the version of each procedure an employee read to the last slide, so the app can mark a new version and the admin can tell who has read it

Revision ID: l7q9i1k3e105
Revises: k6p8h0j2d094
Create Date: 2026-11-07 10:00:00.000000

One row per employee per procedure. The primary key (sop_id, staff_id) also serves the count per procedure; the index on staff_id serves the list of one
employee. The rows belong to the procedure and go with it; accounts are only soft-deleted, so that reference is held back. Every step looks first, so a
second run changes nothing. Down drops the table.
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'l7q9i1k3e105'
down_revision: Union[str, Sequence[str], None] = 'k6p8h0j2d094'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")

TABLE = """
CREATE TABLE IF NOT EXISTS sop_reads (
    read_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    version INTEGER NOT NULL,
    sop_id TEXT NOT NULL,
    staff_id TEXT NOT NULL,
    CONSTRAINT pk_sop_reads PRIMARY KEY (sop_id, staff_id),
    CONSTRAINT check_sop_reads_version_positive CHECK (version > 0)
)
"""

INDEXES = ('CREATE INDEX IF NOT EXISTS index_sop_reads_on_staff_id ON sop_reads (staff_id)',)

FOREIGN_KEYS = (
    ('fk_sop_reads_sop_id_sop', 'sop_id', 'sop', 'CASCADE'),
    ('fk_sop_reads_staff_id_staff', 'staff_id', 'staff', 'RESTRICT'),
)


def _foreign_key(name: str, column: str, target: str, action: str) -> str:
    return f"""
    DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE connamespace = current_schema()::regnamespace AND conname = '{name}') THEN
            ALTER TABLE sop_reads ADD CONSTRAINT {name} FOREIGN KEY ({column}) REFERENCES {target}(id) ON DELETE {action} NOT VALID;
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
        op.execute(f'ALTER TABLE sop_reads VALIDATE CONSTRAINT {name}')


def downgrade() -> None:
    op.execute('DROP TABLE IF EXISTS sop_reads')
