"""roles: the admin role is not protected, so the owner and admins can give it to office staff

Revision ID: c3f5a7b9d104
Revises: b9e1c3d5f702
Create Date: 2026-10-25 15:00:00.000000

A protected role is now never given to an account (app.core.protection.can_give_role); only the owner role stays protected.
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'c3f5a7b9d104'
down_revision: Union[str, Sequence[str], None] = 'b9e1c3d5f702'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE roles SET is_protected = false WHERE id = 'admin'")


def downgrade() -> None:
    # Whether admin was protected before is not known, so going back leaves it as it is.
    pass
