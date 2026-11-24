"""remove camera and face recognition leftovers: visits.recognition_event_id and the permissions that belonged to them

Revision ID: e6h8a0c2d437
Revises: d5f7b9c1e206
Create Date: 2026-11-02 15:00:00.000000

The system has no camera and no face recognition. Contract step of expand -> migrate -> contract: the code stopped reading
visits.recognition_event_id in the previous release, so the column goes now. The three permissions of the removed features are also taken
out of every role that still holds them (the role screen already drops unknown keys, this just makes the stored data match).
No row is added or removed, so scripts/pra_deploy.py's row-count check is unaffected.
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'e6h8a0c2d437'
down_revision: Union[str, Sequence[str], None] = 'd5f7b9c1e206'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# roles.izin is a JSON array of keys. Only roles that actually hold a removed key are touched, and only when the value is an array.
STRIP_PERMISSIONS = """
UPDATE roles
SET izin = COALESCE(
    (SELECT json_agg(key) FROM json_array_elements_text(roles.izin) AS key WHERE key NOT IN ('kamera.kelola', 'wajah.daftarkan', 'wajah.hapus')),
    '[]'::json
)
WHERE json_typeof(izin) = 'array'
  AND EXISTS (SELECT 1 FROM json_array_elements_text(roles.izin) AS key WHERE key IN ('kamera.kelola', 'wajah.daftarkan', 'wajah.hapus'))
"""


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '1s'")
    op.execute('ALTER TABLE IF EXISTS visits DROP COLUMN IF EXISTS recognition_event_id')
    op.execute(STRIP_PERMISSIONS)


def downgrade() -> None:
    # The dropped column and permission keys held data of features that no longer exist; there is nothing to restore.
    pass
