"""the standard units an ingredient can be measured in, so the ingredient form has something to choose from

Revision ID: t5y7q9s1m983
Revises: s4x6p8r0l872
Create Date: 2026-11-11 10:00:00.000000

The units table had no rows and the web has no screen to add one, so no ingredient could be saved. Each standard unit is inserted only when no unit of that name exists
(compared without regard to letter case), so units that are already there keep their ids and a second run changes nothing. Down does nothing: ingredients and
recipes may already point at these rows, and removing them would break those references.
"""
from typing import Sequence, Union

from alembic import op

revision: str = 't5y7q9s1m983'
down_revision: Union[str, Sequence[str], None] = 's4x6p8r0l872'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")

UNITS = ('gram', 'kg', 'ml', 'liter', 'pcs', 'pack', 'botol', 'kotak')

INSERT = """
    INSERT INTO units (id, name)
    SELECT gen_random_uuid()::text, wanted.name
    FROM (VALUES {values}) AS wanted(name)
    WHERE NOT EXISTS (SELECT 1 FROM units existing WHERE lower(existing.name) = lower(wanted.name))
"""


def upgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    values = ', '.join(f"('{name}')" for name in UNITS)
    op.execute(INSERT.format(values=values))


def downgrade() -> None:
    # Rows that may already be referenced are kept; see the note at the top.
    pass
