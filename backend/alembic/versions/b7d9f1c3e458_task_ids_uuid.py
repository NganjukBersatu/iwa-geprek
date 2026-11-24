"""tasks: ids of tugas and outlet_tasks, and the attachment columns pointing at them, become uuid

Revision ID: b7d9f1c3e458
Revises: a6c8e0b2d347
Create Date: 2026-10-22 13:00:00.000000

The existing values are already uuid text, so they are cast in place; the foreign keys are dropped and rebuilt
around the change because both sides must share one type.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'b7d9f1c3e458'
down_revision: Union[str, Sequence[str], None] = 'a6c8e0b2d347'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PERSONAL_FK = 'task_attachments_personal_task_id_fkey'
OUTLET_FK = 'task_attachments_outlet_task_id_fkey'


def _retype(new_type: sa.types.TypeEngine, cast: str) -> None:
    op.drop_constraint(PERSONAL_FK, 'task_attachments', type_='foreignkey')
    op.drop_constraint(OUTLET_FK, 'task_attachments', type_='foreignkey')
    for table, column in (
        ('tugas', 'id'),
        ('outlet_tasks', 'id'),
        ('task_attachments', 'personal_task_id'),
        ('task_attachments', 'outlet_task_id'),
    ):
        op.alter_column(table, column, type_=new_type, postgresql_using=f'{column}::{cast}')
    op.create_foreign_key(PERSONAL_FK, 'task_attachments', 'tugas', ['personal_task_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(OUTLET_FK, 'task_attachments', 'outlet_tasks', ['outlet_task_id'], ['id'], ondelete='CASCADE')


def upgrade() -> None:
    _retype(sa.Uuid(), 'uuid')


def downgrade() -> None:
    _retype(sa.String(), 'varchar')
