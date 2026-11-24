"""expense ingredient: a receipt line may name one of the branch's ingredients, with how much and in which unit; money only, stock is untouched

Revision ID: e5g7b9d1f326
Revises: c3f5a7b9d104
Create Date: 2026-10-25 15:00:00.000000

Expand only: three new nullable columns, so every expense recorded before stays a plain line.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'e5g7b9d1f326'
down_revision: Union[str, Sequence[str], None] = 'c3f5a7b9d104'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('expenses', sa.Column('bahan_id', sa.String(), sa.ForeignKey('bahan.id', ondelete='SET NULL'), nullable=True))
    op.add_column('expenses', sa.Column('qty', sa.Numeric(12, 3), nullable=True))
    op.add_column('expenses', sa.Column('satuan_id', sa.String(), sa.ForeignKey('satuan.id', ondelete='SET NULL'), nullable=True))


def downgrade() -> None:
    op.drop_column('expenses', 'satuan_id')
    op.drop_column('expenses', 'qty')
    op.drop_column('expenses', 'bahan_id')
