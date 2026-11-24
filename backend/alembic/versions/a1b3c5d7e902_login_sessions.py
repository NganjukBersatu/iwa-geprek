"""login sessions: one row per sign-in, so a token can be cut off on sign-out, password change, or account deactivation

Revision ID: a1b3c5d7e902
Revises: e5g7b9d1f326
Create Date: 2026-10-26 20:00:00.000000

Expand only: a new table; tokens issued before it carry no session and stay valid until they expire.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'a1b3c5d7e902'
down_revision: Union[str, Sequence[str], None] = 'e5g7b9d1f326'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'login_sessions',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('staff_id', sa.String(), sa.ForeignKey('staff.id', ondelete='CASCADE'), nullable=False),
        sa.Column('channel', sa.String(16), nullable=False),
        sa.Column('device_label', sa.String(160), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_login_sessions_staff', 'login_sessions', ['staff_id'])


def downgrade() -> None:
    op.drop_index('ix_login_sessions_staff', table_name='login_sessions')
    op.drop_table('login_sessions')
