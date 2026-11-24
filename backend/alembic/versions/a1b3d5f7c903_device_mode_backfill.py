"""mode tablet lama: tablet yang hanya memegang Kasir menjadi Mode Kasir

Revision ID: a1b3d5f7c903
Revises: a1b3d5f7c902
Create Date: 2026-11-24 22:05:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'a1b3d5f7c903'
down_revision: Union[str, Sequence[str], None] = 'a1b3d5f7c902'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")

# Tablet yang memegang Kasir tanpa stasiun pembuat atau pengantar sudah mencetak stasiun tanpa tablet saat pesanan dibuat, jadi perilakunya tidak berubah.
BACKFILL = """
UPDATE devices d
SET mode = 'cashier'
WHERE d.mode = 'station'
  AND EXISTS (
      SELECT 1 FROM device_stations ds JOIN stations s ON s.id = ds.station_id
      WHERE ds.device_id = d.id AND s.kind = 'handover'
  )
  AND NOT EXISTS (
      SELECT 1 FROM device_stations ds JOIN stations s ON s.id = ds.station_id
      WHERE ds.device_id = d.id AND s.kind IN ('make', 'deliver')
  )
"""


def upgrade() -> None:
    for statement in (*TIMEOUTS, BACKFILL):
        op.execute(statement)


def downgrade() -> None:
    """Kolomnya dihapus migrasi sebelumnya bila dibalik lebih jauh; di sini mode dikembalikan ke bawaan lama."""
    for statement in TIMEOUTS:
        op.execute(statement)
    op.execute("UPDATE devices SET mode = 'station' WHERE mode = 'cashier'")
