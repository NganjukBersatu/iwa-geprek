"""perbaiki trigger jejak uang: kolom berubah ditambah dengan array_append, bukan operator ||

Revision ID: d5f7b9c1e206
Revises: c3e5a7b9d104
Create Date: 2026-10-30 09:00:00.000000
"""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Sequence, Union

from alembic import op

revision: str = 'd5f7b9c1e206'
down_revision: Union[str, Sequence[str], None] = 'c3e5a7b9d104'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TRIGGER_FUNCTIONS = (
    'MONEY_ORDER_CHANGE',
    'MONEY_EXPENSE_CHANGE',
    'MONEY_OVERPAYMENT_CHANGE',
    'MONEY_SESSION_CHANGE',
)


def upgrade() -> None:
    # Fungsi di database yang sudah terpasang masih memakai `changed || 'teks'`; isi sumbernya satu, di migrasi rilis Oktober.
    source = Path(__file__).with_name('c3e5a7b9d104_release_2026_10.py')
    spec = spec_from_file_location('release_2026_10', source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'migrasi rilis tidak bisa dimuat: {source}')
    release = module_from_spec(spec)
    spec.loader.exec_module(release)
    op.execute("SET LOCAL lock_timeout = '1s'")
    for name in TRIGGER_FUNCTIONS:
        op.execute(getattr(release, name))


def downgrade() -> None:
    # Fungsi lama berisi galat; tidak ada keadaan sebelumnya yang layak dipulihkan.
    pass
