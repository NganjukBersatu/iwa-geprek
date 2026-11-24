"""login attempts: wrong passwords counted per username, so guessing one account's password is slowed down

Revision ID: f8j0b2d4e548
Revises: e6h8a0c2d437
Create Date: 2026-11-02 18:00:00.000000

Expand only: one new table, nothing existing is touched. The key is the SHA-256 of the lower-cased username (see app.auth.attempts), with no
foreign key on purpose, so a name that does not exist is counted exactly like one that does.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'f8j0b2d4e548'
down_revision: Union[str, Sequence[str], None] = 'e6h8a0c2d437'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'login_attempts',
        sa.Column('username_hash', sa.String(length=64), nullable=False),
        sa.Column('failures', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('lockouts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('window_started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('username_hash', name='pk_login_attempts'),
        sa.CheckConstraint('char_length(username_hash) = 64', name='check_login_attempts_username_hash_length'),
        sa.CheckConstraint('failures >= 0', name='check_login_attempts_failures_range'),
        sa.CheckConstraint('lockouts >= 0', name='check_login_attempts_lockouts_range'),
    )
    # Serves the cleanup of rows that have been quiet for a day.
    op.create_index('index_login_attempts_on_updated_at', 'login_attempts', ['updated_at'])


def downgrade() -> None:
    op.drop_index('index_login_attempts_on_updated_at', table_name='login_attempts')
    op.drop_table('login_attempts')
