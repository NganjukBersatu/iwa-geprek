"""remove the registered-customer feature: orders.customer_id, the visits and customers tables, and the permissions that went with them

Revision ID: h1l2d4f6a760
Revises: g0k1c3e5f659
Create Date: 2026-11-02 21:00:00.000000

The system has no customer app and no camera, so nothing creates a registered customer any more and no code reads them. This is the contract
step: the code stopped using them first. What is lost for good: the customers table (names, contacts, notes) and every visit row. The free-text
name typed on an order (orders.customer_name) is a different thing and stays.

The tables are dropped without CASCADE on purpose: if anything else still points at them (a leftover table of the old backend), this fails and
rolls the whole deploy back, instead of silently dropping that too. app.core.migration_check lists both tables as removed on purpose, so the
deploy guard does not read their disappearance as lost data.

Each step looks first, so a database built from the base revisions (which never had these tables) passes through unchanged.
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'h1l2d4f6a760'
down_revision: Union[str, Sequence[str], None] = 'g0k1c3e5f659'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# roles.izin is a JSON array of keys; only roles that hold a removed key are touched.
STRIP_PERMISSIONS = """
UPDATE roles
SET izin = COALESCE(
    (SELECT json_agg(key) FROM json_array_elements_text(roles.izin) AS key
     WHERE key NOT IN ('pelanggan.lihat', 'pelanggan.kelola', 'pelanggan.hapus', 'kunjungan.hapus', 'mitra.kelola')),
    '[]'::json
)
WHERE json_typeof(izin) = 'array'
  AND EXISTS (
      SELECT 1 FROM json_array_elements_text(roles.izin) AS key
      WHERE key IN ('pelanggan.lihat', 'pelanggan.kelola', 'pelanggan.hapus', 'kunjungan.hapus', 'mitra.kelola')
  )
"""


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '1s'")
    # The column first: dropping it also drops its foreign key to customers, which the table drop below would otherwise trip over.
    op.execute('ALTER TABLE orders DROP COLUMN IF EXISTS customer_id')
    op.execute('DROP TABLE IF EXISTS visits')
    op.execute('DROP TABLE IF EXISTS customers')
    op.execute(STRIP_PERMISSIONS)


def downgrade() -> None:
    # The dropped rows held personal data of a feature that no longer exists; there is nothing to restore.
    pass
