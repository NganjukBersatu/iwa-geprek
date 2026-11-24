"""login_sessions.last_seen_at: lets the server end a browser sign-in that has been idle too long

Revision ID: i3m5e7g9b871
Revises: h1l2d4f6a760
Create Date: 2026-11-03 14:00:00.000000

Expand step: the column has a default, so the running release, which does not write it, keeps working. Every sign-in made before this
release carries a token without the claims the new code requires, so it is refused and people sign in again once.
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'i3m5e7g9b871'
down_revision: Union[str, Sequence[str], None] = 'h1l2d4f6a760'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '1s'")
    op.execute('ALTER TABLE login_sessions ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()')


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '1s'")
    op.execute('ALTER TABLE login_sessions DROP COLUMN IF EXISTS last_seen_at')
