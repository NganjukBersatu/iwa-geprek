"""a unit name can exist only once, whatever its letter case, so the ingredient form never offers two units that look the same

Revision ID: u6z8r0t2n094
Revises: t5y7q9s1m983
Create Date: 2026-11-11 12:00:00.000000

The unique index is on the lowercased name, so "Gram" and "gram" are the same unit. The step first looks for names that already exist twice; if it finds any it stops
with the list and changes nothing, because merging them means moving every ingredient and recipe that points at the duplicate, which is a decision for a person.
The table holds a handful of rows, so the index is built in the same transaction under a short lock timeout; every step looks first, so a second run changes nothing.
Down drops the index.
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'u6z8r0t2n094'
down_revision: Union[str, Sequence[str], None] = 't5y7q9s1m983'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")

STEPS = (
    """
    DO $$
    DECLARE clashing text;
    BEGIN
        SELECT string_agg(DISTINCT lower(name), ', ') INTO clashing
        FROM units
        WHERE lower(name) IN (SELECT lower(name) FROM units GROUP BY lower(name) HAVING count(*) > 1);
        IF clashing IS NOT NULL THEN
            RAISE EXCEPTION 'Satuan dengan nama ganda: %. Gabungkan atau hapus yang ganda lebih dulu, lalu jalankan ulang.', clashing;
        END IF;
    END $$;
    """,
    'CREATE UNIQUE INDEX IF NOT EXISTS unique_units_name ON units (lower(name))',
)


def upgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    for statement in STEPS:
        op.execute(statement)


def downgrade() -> None:
    op.execute('DROP INDEX IF EXISTS unique_units_name')
