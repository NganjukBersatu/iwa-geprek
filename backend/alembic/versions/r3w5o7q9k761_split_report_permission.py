"""split the single report permission into one permission for each report and each dashboard card

Revision ID: r3w5o7q9k761
Revises: q2v4n6p8j650
Create Date: 2026-11-10 18:00:00.000000

Every role that held `laporan.lihat` receives all the new report permissions in the same step and loses the old key, so nobody sees less than before and the roles
screen can narrow each role afterwards. The step reads the roles first, so a second run finds nothing left to change. The full-access roles hold every permission in the
catalog by definition and are unaffected. Down puts `laporan.lihat` back on every role that holds the dashboard summary permission; the new keys stay, since the
previous version ignores keys it does not know.
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'r3w5o7q9k761'
down_revision: Union[str, Sequence[str], None] = 'q2v4n6p8j650'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")

NEW_KEYS = (
    'laporan.ringkasan',
    'laporan.tren',
    'laporan.laba_rugi',
    'laporan.nilai_persediaan',
    'laporan.kasir',
    'laporan.perbandingan',
    'laporan.transaksi',
    'laporan.overview',
    'laporan.ramai_penjualan',
    'laporan.ramai_produk',
    'laporan.kategori',
    'laporan.varian_ekstra',
    'laporan.promo',
    'laporan.batal',
    'laporan.pengunjung',
    'laporan.stok_bahan',
    'laporan.perputaran',
    'laporan.kehadiran',
    'laporan.margin',
    'laporan.kinerja_stasiun',
)

_KEYS_SQL = ', '.join("'%s'" % key for key in NEW_KEYS)

SPLIT = f"""
UPDATE roles
SET permissions = (
    SELECT COALESCE(jsonb_agg(DISTINCT to_jsonb(item.key)), '[]'::jsonb)
    FROM (
        SELECT jsonb_array_elements_text(roles.permissions::jsonb) AS key
        UNION
        SELECT unnest(ARRAY[{_KEYS_SQL}])
    ) AS item
    WHERE item.key <> 'laporan.lihat'
)::json
WHERE roles.permissions::jsonb @> '["laporan.lihat"]'::jsonb
"""

MERGE_BACK = """
UPDATE roles
SET permissions = (roles.permissions::jsonb || '["laporan.lihat"]'::jsonb)::json
WHERE roles.permissions::jsonb @> '["laporan.ringkasan"]'::jsonb
  AND NOT roles.permissions::jsonb @> '["laporan.lihat"]'::jsonb
"""


def upgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    op.execute(SPLIT)


def downgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    op.execute(MERGE_BACK)
