"""roles: is_admin marks a supervising role, which a self-made schedule cannot pick

Revision ID: c8e0a2b4f569
Revises: b7d9f1c3e458
Create Date: 2026-10-22 15:00:00.000000

Owner and admin are marked during the upgrade; other roles are marked from the role page.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'c8e0a2b4f569'
down_revision: Union[str, Sequence[str], None] = 'b7d9f1c3e458'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('roles', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.execute("UPDATE roles SET is_admin = true WHERE id IN ('owner', 'admin')")


def downgrade() -> None:
    op.drop_column('roles', 'is_admin')
