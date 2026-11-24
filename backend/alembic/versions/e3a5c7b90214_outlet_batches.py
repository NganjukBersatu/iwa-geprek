"""batches: checklists defined by an admin per branch, with their finished runs

Revision ID: e3a5c7b90214
Revises: d2f4a6c8e013
Create Date: 2026-10-18 16:00:00.000000

Adds four tables only; nothing the legacy backend reads is touched.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'e3a5c7b90214'
down_revision: Union[str, Sequence[str], None] = 'd2f4a6c8e013'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'outlet_batches',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('outlet_id', sa.String(), sa.ForeignKey('outlets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('start_clock', sa.String(length=5), nullable=False),
        sa.Column('end_clock', sa.String(length=5), nullable=False),
        sa.Column('weekdays', sa.String(length=13), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_outlet_batches_outlet_id', 'outlet_batches', ['outlet_id'])

    op.create_table(
        'outlet_batch_items',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('batch_id', sa.String(), sa.ForeignKey('outlet_batches.id', ondelete='CASCADE'), nullable=False),
        sa.Column('label', sa.String(length=200), nullable=False),
        sa.Column('kind', sa.String(length=10), nullable=False),
        sa.Column('required', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
    )
    op.create_index('ix_outlet_batch_items_batch_id', 'outlet_batch_items', ['batch_id'])

    op.create_table(
        'outlet_batch_runs',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('batch_id', sa.String(), sa.ForeignKey('outlet_batches.id', ondelete='CASCADE'), nullable=False),
        sa.Column('day', sa.Date(), nullable=False),
        sa.Column('completed_by_id', sa.String(), sa.ForeignKey('staff.id', ondelete='SET NULL'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('batch_id', 'day', name='uq_outlet_batch_runs_batch_day'),
    )

    op.create_table(
        'outlet_batch_answers',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('run_id', sa.String(), sa.ForeignKey('outlet_batch_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('item_id', sa.String(), sa.ForeignKey('outlet_batch_items.id', ondelete='SET NULL'), nullable=True),
        sa.Column('item_label', sa.String(length=200), nullable=False),
        sa.Column('item_kind', sa.String(length=10), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('photo_path', sa.String(length=500), nullable=True),
    )
    op.create_index('ix_outlet_batch_answers_run_id', 'outlet_batch_answers', ['run_id'])


def downgrade() -> None:
    op.drop_index('ix_outlet_batch_answers_run_id', table_name='outlet_batch_answers')
    op.drop_table('outlet_batch_answers')
    op.drop_table('outlet_batch_runs')
    op.drop_index('ix_outlet_batch_items_batch_id', table_name='outlet_batch_items')
    op.drop_table('outlet_batch_items')
    op.drop_index('ix_outlet_batches_outlet_id', table_name='outlet_batches')
    op.drop_table('outlet_batches')
