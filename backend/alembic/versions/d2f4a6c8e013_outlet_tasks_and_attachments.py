"""tasks: branch tasks and photo/video attachments

Revision ID: d2f4a6c8e013
Revises: a0b1c2d3e404
Create Date: 2026-10-17 12:00:00.000000

First migration of the v2 chain on a database that already had the core tables (table alembic_version_v2). It only adds two tables: the
existing tugas table and everything the legacy backend reads stay untouched. A database built from nothing gets those core tables from the
four a0b1c2d3e40x base revisions that now come before this one.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'd2f4a6c8e013'
down_revision: Union[str, Sequence[str], None] = 'a0b1c2d3e404'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'outlet_tasks',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('outlet_id', sa.String(), sa.ForeignKey('outlets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_id', sa.String(), sa.ForeignKey('staff.id', ondelete='SET NULL'), nullable=True),
        sa.Column('completed_by_id', sa.String(), sa.ForeignKey('staff.id', ondelete='SET NULL'), nullable=True),
        sa.Column('completion_note', sa.Text(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_outlet_tasks_outlet_id', 'outlet_tasks', ['outlet_id'])
    op.create_index('ix_outlet_tasks_completed_at', 'outlet_tasks', ['completed_at'])

    op.create_table(
        'task_attachments',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('personal_task_id', sa.String(), sa.ForeignKey('tugas.id', ondelete='CASCADE'), nullable=True),
        sa.Column('outlet_task_id', sa.String(), sa.ForeignKey('outlet_tasks.id', ondelete='CASCADE'), nullable=True),
        sa.Column('kind', sa.String(length=10), nullable=False),
        sa.Column('path', sa.String(length=500), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_by_id', sa.String(), sa.ForeignKey('staff.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            '(personal_task_id IS NOT NULL) <> (outlet_task_id IS NOT NULL)',
            name='ck_task_attachments_one_owner',
        ),
    )
    op.create_index('ix_task_attachments_personal_task_id', 'task_attachments', ['personal_task_id'])
    op.create_index('ix_task_attachments_outlet_task_id', 'task_attachments', ['outlet_task_id'])


def downgrade() -> None:
    op.drop_index('ix_task_attachments_outlet_task_id', table_name='task_attachments')
    op.drop_index('ix_task_attachments_personal_task_id', table_name='task_attachments')
    op.drop_table('task_attachments')
    op.drop_index('ix_outlet_tasks_completed_at', table_name='outlet_tasks')
    op.drop_index('ix_outlet_tasks_outlet_id', table_name='outlet_tasks')
    op.drop_table('outlet_tasks')
