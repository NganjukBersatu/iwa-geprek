"""notices: what to tell each employee when they sign in

Revision ID: a6c8e0b2d347
Revises: f4b6d8e0a125
Create Date: 2026-10-22 12:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'a6c8e0b2d347'
down_revision: Union[str, Sequence[str], None] = 'f4b6d8e0a125'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'notices',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('staff_id', sa.String(), sa.ForeignKey('staff.id', ondelete='CASCADE'), nullable=False),
        sa.Column('kind', sa.String(), nullable=False),
        sa.Column('task_kind', sa.String(), nullable=True),
        sa.Column('task_id', sa.Uuid(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('show_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_notices_staff_id', 'notices', ['staff_id'])
    op.create_index('ix_notices_show_at', 'notices', ['show_at'])


def downgrade() -> None:
    op.drop_index('ix_notices_show_at', table_name='notices')
    op.drop_index('ix_notices_staff_id', table_name='notices')
    op.drop_table('notices')
