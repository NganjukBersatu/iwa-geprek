"""the account that created a role, so the creator can still change a protected role it made

Revision ID: s4x6p8r0l872
Revises: r3w5o7q9k761
Create Date: 2026-11-10 20:00:00.000000

A protected role may be changed by the accounts holding it and by the account that created it; no one may delete it. Roles that exist already have no creator
(they stay empty), so only their holders can change them, as before. The reference is only emptied when the account goes, since the role outlives its creator.
The foreign key is added without validation and validated in a step of its own; every step looks first, so a second run changes nothing. Down drops the column.
"""
from typing import Sequence, Union

from alembic import op

revision: str = 's4x6p8r0l872'
down_revision: Union[str, Sequence[str], None] = 'r3w5o7q9k761'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")

STEPS = (
    'ALTER TABLE roles ADD COLUMN IF NOT EXISTS created_by TEXT',
    'CREATE INDEX IF NOT EXISTS index_roles_on_created_by ON roles (created_by)',
    """
    DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE connamespace = current_schema()::regnamespace AND conname = 'fk_roles_created_by_staff') THEN
            ALTER TABLE roles ADD CONSTRAINT fk_roles_created_by_staff FOREIGN KEY (created_by) REFERENCES staff(id) ON DELETE SET NULL NOT VALID;
        END IF;
    END $$;
    """,
    'ALTER TABLE roles VALIDATE CONSTRAINT fk_roles_created_by_staff',
)


def upgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    for statement in STEPS:
        op.execute(statement)


def downgrade() -> None:
    op.execute('ALTER TABLE roles DROP CONSTRAINT IF EXISTS fk_roles_created_by_staff')
    op.execute('DROP INDEX IF EXISTS index_roles_on_created_by')
    op.execute('ALTER TABLE roles DROP COLUMN IF EXISTS created_by')
