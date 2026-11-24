"""index on the expense receipt photo: one photographed receipt backs several expenses, and its file is removed only when none points at it

Revision ID: a7c9e1b3d528
Revises: d4f6a8c0e215
Create Date: 2026-10-24 21:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'a7c9e1b3d528'
down_revision: Union[str, Sequence[str], None] = 'd4f6a8c0e215'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE INDEX IF NOT EXISTS ix_expenses_bukti_path ON expenses (bukti_path) WHERE bukti_path IS NOT NULL')


def downgrade() -> None:
    op.execute('DROP INDEX IF EXISTS ix_expenses_bukti_path')
