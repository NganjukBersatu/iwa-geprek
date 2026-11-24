"""expense receipt path index: finds the purchases that share one receipt photo, so the file can be opened only by staff allowed to see them

Revision ID: m8r0j2l4f216
Revises: l7q9i1k3e105
Create Date: 2026-11-08 09:00:00.000000

The shared receipt route looks expenses up by the stored path; without the index that is a full scan of a table that only grows. The index is partial because most
rows have no photo. It is built inside the pre-deploy transaction (a concurrent build cannot run there), which is safe while the table is small; Down drops the index.
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'm8r0j2l4f216'
down_revision: Union[str, Sequence[str], None] = 'l7q9i1k3e105'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEX = 'index_expenses_on_receipt_path'


def upgrade() -> None:
    op.execute(f'CREATE INDEX IF NOT EXISTS {INDEX} ON expenses (receipt_path) WHERE receipt_path IS NOT NULL')


def downgrade() -> None:
    op.execute(f'DROP INDEX IF EXISTS {INDEX}')
