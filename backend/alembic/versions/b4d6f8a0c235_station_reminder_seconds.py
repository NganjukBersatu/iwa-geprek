"""jeda bunyi pengingat per stasiun per cabang: 0 mematikan pengingat, selain itu 15 detik sampai 10 menit, bawaan 60 detik

Revision ID: b4d6f8a0c235
Revises: x9d1u3w5q327
Create Date: 2026-11-07 17:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'b4d6f8a0c235'
down_revision: Union[str, Sequence[str], None] = 'x9d1u3w5q327'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")

CONSTRAINT = 'check_station_branch_settings_reminder_seconds_range'


def upgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    # Nilai bawaan 60 membuat cabang yang sudah ada langsung memakai pengingat tanpa mengisi ulang satu per satu.
    op.execute('ALTER TABLE station_branch_settings ADD COLUMN IF NOT EXISTS reminder_seconds INTEGER NOT NULL DEFAULT 60')
    op.execute(
        f"""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '{CONSTRAINT}') THEN
                ALTER TABLE station_branch_settings ADD CONSTRAINT {CONSTRAINT}
                    CHECK (reminder_seconds = 0 OR reminder_seconds BETWEEN 15 AND 600) NOT VALID;
            END IF;
        END $$;
        """
    )
    op.execute(f'ALTER TABLE station_branch_settings VALIDATE CONSTRAINT {CONSTRAINT}')


def downgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    op.execute(f'ALTER TABLE station_branch_settings DROP CONSTRAINT IF EXISTS {CONSTRAINT}')
    op.execute('ALTER TABLE station_branch_settings DROP COLUMN IF EXISTS reminder_seconds')
