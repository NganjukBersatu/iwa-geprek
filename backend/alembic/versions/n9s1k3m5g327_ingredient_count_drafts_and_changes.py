"""ingredient count drafts, the trail of changes to closed counts, and where a count was closed

Revision ID: n9s1k3m5g327
Revises: m8r0j2l4f216
Create Date: 2026-11-10 09:00:00.000000

A draft holds the counted figure typed for a branch's next count until the period is closed, shared by the web and the tablet. The change trail outlives the
count it came from, so its parents are only emptied, never cascaded. `source` tells whether a count was closed on the web or on the tablet; older counts are web.
Every step looks first, so a second run changes nothing; foreign keys and the check are added without validation and validated in a step of their own.
Down drops the tables and the column.
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'n9s1k3m5g327'
down_revision: Union[str, Sequence[str], None] = 'm8r0j2l4f216'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")

CHANGES_TABLE = """
CREATE TABLE IF NOT EXISTS ingredient_count_changes (
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    id TEXT NOT NULL,
    outlet_id TEXT NOT NULL,
    count_id TEXT,
    ingredient_id TEXT,
    staff_id TEXT,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    ingredient_name TEXT NOT NULL,
    action TEXT NOT NULL,
    old_counted NUMERIC(12, 3),
    new_counted NUMERIC(12, 3),
    CONSTRAINT pk_ingredient_count_changes PRIMARY KEY (id),
    CONSTRAINT check_ingredient_count_changes_action_enum CHECK (action IN ('set', 'remove')),
    CONSTRAINT check_ingredient_count_changes_ingredient_name_length CHECK (char_length(ingredient_name) BETWEEN 1 AND 255),
    CONSTRAINT check_ingredient_count_changes_period_order CHECK (period_end >= period_start)
)
"""

DRAFTS_TABLE = """
CREATE TABLE IF NOT EXISTS ingredient_count_drafts (
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    outlet_id TEXT NOT NULL,
    ingredient_id TEXT NOT NULL,
    staff_id TEXT,
    counted NUMERIC(12, 3) NOT NULL,
    CONSTRAINT pk_ingredient_count_drafts PRIMARY KEY (outlet_id, ingredient_id),
    CONSTRAINT check_ingredient_count_drafts_counted_range CHECK (counted >= 0 AND counted <= 999999999)
)
"""

INDEXES = (
    'CREATE INDEX IF NOT EXISTS index_ingredient_count_changes_on_count_id_and_created_at ON ingredient_count_changes (count_id, created_at DESC)',
    'CREATE INDEX IF NOT EXISTS index_ingredient_count_changes_on_outlet_id ON ingredient_count_changes (outlet_id)',
    'CREATE INDEX IF NOT EXISTS index_ingredient_count_changes_on_ingredient_id ON ingredient_count_changes (ingredient_id)',
    'CREATE INDEX IF NOT EXISTS index_ingredient_count_changes_on_staff_id ON ingredient_count_changes (staff_id)',
    'CREATE INDEX IF NOT EXISTS index_ingredient_count_drafts_on_ingredient_id ON ingredient_count_drafts (ingredient_id)',
    'CREATE INDEX IF NOT EXISTS index_ingredient_count_drafts_on_staff_id ON ingredient_count_drafts (staff_id)',
)

# A draft belongs to its branch and ingredient and goes with them; its writer is only emptied. The audit trail never cascades.
FOREIGN_KEYS = (
    ('ingredient_count_drafts', 'fk_ingredient_count_drafts_outlet_id_outlets', 'outlet_id', 'outlets', 'CASCADE'),
    ('ingredient_count_drafts', 'fk_ingredient_count_drafts_ingredient_id_ingredients', 'ingredient_id', 'ingredients', 'CASCADE'),
    ('ingredient_count_drafts', 'fk_ingredient_count_drafts_staff_id_staff', 'staff_id', 'staff', 'SET NULL'),
    ('ingredient_count_changes', 'fk_ingredient_count_changes_outlet_id_outlets', 'outlet_id', 'outlets', 'RESTRICT'),
    ('ingredient_count_changes', 'fk_ingredient_count_changes_count_id_ingredient_counts', 'count_id', 'ingredient_counts', 'SET NULL'),
    ('ingredient_count_changes', 'fk_ingredient_count_changes_ingredient_id_ingredients', 'ingredient_id', 'ingredients', 'SET NULL'),
    ('ingredient_count_changes', 'fk_ingredient_count_changes_staff_id_staff', 'staff_id', 'staff', 'SET NULL'),
)

SOURCE = (
    "ALTER TABLE ingredient_counts ADD COLUMN IF NOT EXISTS source TEXT NOT NULL DEFAULT 'web'",
    """
    DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE connamespace = current_schema()::regnamespace AND conname = 'check_ingredient_counts_source_enum') THEN
            ALTER TABLE ingredient_counts ADD CONSTRAINT check_ingredient_counts_source_enum CHECK (source IN ('web', 'tablet')) NOT VALID;
        END IF;
    END $$;
    """,
    'ALTER TABLE ingredient_counts VALIDATE CONSTRAINT check_ingredient_counts_source_enum',
)

DROP_SOURCE = (
    'ALTER TABLE ingredient_counts DROP CONSTRAINT IF EXISTS check_ingredient_counts_source_enum',
    'ALTER TABLE ingredient_counts DROP COLUMN IF EXISTS source',
)


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
    op.execute(CHANGES_TABLE)
    op.execute(DRAFTS_TABLE)
    for statement in INDEXES:
        op.execute(statement)
    for table, name, column, target, action in FOREIGN_KEYS:
        op.execute(_foreign_key(table, name, column, target, action))
    for table, name, _column, _target, _action in FOREIGN_KEYS:
        op.execute(f'ALTER TABLE {table} VALIDATE CONSTRAINT {name}')
    for statement in SOURCE:
        op.execute(statement)


def downgrade() -> None:
    op.execute('DROP TABLE IF EXISTS ingredient_count_drafts')
    op.execute('DROP TABLE IF EXISTS ingredient_count_changes')
    for statement in DROP_SOURCE:
        op.execute(statement)
