"""deposits: cash handed over to the owner, and which income days each deposit settled

Revision ID: b1d3f5a7c902
Revises: a9c1e3f5b702
Create Date: 2026-10-24 15:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'b1d3f5a7c902'
down_revision: Union[str, Sequence[str], None] = 'a9c1e3f5b702'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'deposits',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('outlet_id', sa.String(), sa.ForeignKey('outlets.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('deposit_date', sa.Date(), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('note', sa.String(255), nullable=True),
        sa.Column('photo_path', sa.String(500), nullable=True),
        sa.Column('staff_id', sa.String(), sa.ForeignKey('staff.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_deposits_outlet_date', 'deposits', ['outlet_id', 'deposit_date'])
    op.create_table(
        'deposit_days',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('deposit_id', sa.String(), sa.ForeignKey('deposits.id', ondelete='CASCADE'), nullable=False),
        sa.Column('day', sa.Date(), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.UniqueConstraint('deposit_id', 'day', name='uq_deposit_days_deposit_day'),
    )
    op.create_index('ix_deposit_days_day', 'deposit_days', ['day'])


def downgrade() -> None:
    op.drop_index('ix_deposit_days_day', table_name='deposit_days')
    op.drop_table('deposit_days')
    op.drop_index('ix_deposits_outlet_date', table_name='deposits')
    op.drop_table('deposits')
