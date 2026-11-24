"""order notes owned by a branch: an outlet_id on categories, and a note name that is unique per branch

Revision ID: q2v4n6p8j650
Revises: p1u3m5o7i549
Create Date: 2026-11-10 16:00:00.000000

An empty outlet_id is a general note of the old kind that applies to every branch; only the order-note kind may belong to a branch. The new unique index exists
before the old one is dropped, so uniqueness is never missing. The index is built inside the pre-deploy transaction (a concurrent build cannot run there), which is
safe because the categories table is small. Every step looks first, so a second run changes nothing. Down does nothing: two branches may now hold notes with the
same name, so the old global index cannot be put back without deleting data, and the new column and index do not disturb the previous version.
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'q2v4n6p8j650'
down_revision: Union[str, Sequence[str], None] = 'p1u3m5o7i549'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")

STRUCTURE = (
    'ALTER TABLE categories ADD COLUMN IF NOT EXISTS outlet_id TEXT',
    """
    DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE connamespace = current_schema()::regnamespace AND conname = 'fk_categories_outlet_id_outlets') THEN
            ALTER TABLE categories ADD CONSTRAINT fk_categories_outlet_id_outlets FOREIGN KEY (outlet_id) REFERENCES outlets(id) ON DELETE RESTRICT NOT VALID;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE connamespace = current_schema()::regnamespace AND conname = 'check_categories_outlet_id_notes_only') THEN
            ALTER TABLE categories ADD CONSTRAINT check_categories_outlet_id_notes_only CHECK (outlet_id IS NULL OR kind = 'catatan_order') NOT VALID;
        END IF;
    END $$;
    """,
    'ALTER TABLE categories VALIDATE CONSTRAINT fk_categories_outlet_id_outlets',
    'ALTER TABLE categories VALIDATE CONSTRAINT check_categories_outlet_id_notes_only',
)

INDEXES = (
    'CREATE INDEX IF NOT EXISTS index_categories_on_outlet_id ON categories (outlet_id)',
    "CREATE UNIQUE INDEX IF NOT EXISTS unique_categories_kind_outlet_name ON categories (kind, COALESCE(outlet_id, ''), lower(name))",
)

# The old global index is found by what it covers, since the rename of the tables and columns may have given it a name of its own.
DROP_OLD_UNIQUE = """
DO $$
DECLARE found record;
BEGIN
    FOR found IN
        SELECT i.relname
        FROM pg_index x
        JOIN pg_class i ON i.oid = x.indexrelid
        WHERE x.indrelid = 'categories'::regclass
          AND x.indisunique
          AND NOT x.indisprimary
          AND i.relname <> 'unique_categories_kind_outlet_name'
          AND pg_get_indexdef(x.indexrelid) ILIKE '%(kind, lower(%'
    LOOP
        EXECUTE format('DROP INDEX %I', found.relname);
    END LOOP;
END $$;
"""


def upgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    for statement in STRUCTURE:
        op.execute(statement)
    for statement in INDEXES:
        op.execute(statement)
    op.execute(DROP_OLD_UNIQUE)


def downgrade() -> None:
    pass
