"""sop: a branch of its own or every branch, who wrote it, and drafts that survive a closed browser

Revision ID: c5e7a9b1d3f6
Revises: b1d3f5a7c902
Create Date: 2026-10-24 18:00:00.000000

Every new column is nullable, so existing procedures stay global and legacy inserts keep working without knowing them.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'c5e7a9b1d3f6'
down_revision: Union[str, Sequence[str], None] = 'b1d3f5a7c902'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sop', sa.Column('outlet_id', sa.String(), sa.ForeignKey('outlets.id', ondelete='CASCADE'), nullable=True))
    op.add_column('sop', sa.Column('dibuat_oleh', sa.String(), sa.ForeignKey('staff.id', ondelete='SET NULL'), nullable=True))
    op.add_column('sop', sa.Column('diubah_oleh', sa.String(), sa.ForeignKey('staff.id', ondelete='SET NULL'), nullable=True))
    op.create_index('ix_sop_outlet_id', 'sop', ['outlet_id'])
    op.create_table(
        'sop_draf',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('staff_id', sa.String(), sa.ForeignKey('staff.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sop_id', sa.String(), sa.ForeignKey('sop.id', ondelete='CASCADE'), nullable=True),
        sa.Column('versi_dasar', sa.Integer(), nullable=True),
        sa.Column('isi', sa.Text(), nullable=False),
        sa.Column('diperbarui_pada', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_sop_draf_staff_id', 'sop_draf', ['staff_id'])
    # One draft per person per procedure; drafts of procedures not saved yet have no sop_id and may be many.
    op.create_index('uq_sop_draf_staff_sop', 'sop_draf', ['staff_id', 'sop_id'], unique=True, postgresql_where=sa.text('sop_id IS NOT NULL'))


def downgrade() -> None:
    op.drop_index('uq_sop_draf_staff_sop', table_name='sop_draf')
    op.drop_index('ix_sop_draf_staff_id', table_name='sop_draf')
    op.drop_table('sop_draf')
    op.drop_index('ix_sop_outlet_id', table_name='sop')
    op.drop_column('sop', 'diubah_oleh')
    op.drop_column('sop', 'dibuat_oleh')
    op.drop_column('sop', 'outlet_id')
