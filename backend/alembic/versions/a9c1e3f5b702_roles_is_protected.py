"""roles: is_protected locks a role and its accounts to the people who hold that role

Revision ID: a9c1e3f5b702
Revises: c8e0a2b4f569
Create Date: 2026-10-24 12:00:00.000000

The owner role starts protected; any other role is marked from the role page by a holder of a protected role.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'a9c1e3f5b702'
down_revision: Union[str, Sequence[str], None] = 'c8e0a2b4f569'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('roles', sa.Column('is_protected', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.execute("UPDATE roles SET is_protected = true WHERE id = 'owner'")


def downgrade() -> None:
    op.drop_column('roles', 'is_protected')
