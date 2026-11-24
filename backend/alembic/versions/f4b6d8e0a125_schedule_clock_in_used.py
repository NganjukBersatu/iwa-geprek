"""schedule: clock_in_used marks an assignment that already has its clock-in

Revision ID: f4b6d8e0a125
Revises: e3a5c7b90214
Create Date: 2026-10-21 20:00:00.000000

Adds one column to jadwal_shift with a server default, so legacy inserts keep working without knowing it.
Assignments that already have a clock-in are marked during the upgrade.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'f4b6d8e0a125'
down_revision: Union[str, Sequence[str], None] = 'e3a5c7b90214'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'jadwal_shift',
        sa.Column('clock_in_used', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.execute(
        """
        UPDATE jadwal_shift SET clock_in_used = true
        WHERE id IN (
            SELECT jadwal_id FROM absensi WHERE jadwal_id IS NOT NULL AND jam_masuk IS NOT NULL
        )
        """
    )


def downgrade() -> None:
    op.drop_column('jadwal_shift', 'clock_in_used')
