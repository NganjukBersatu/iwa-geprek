"""erase the plaintext passwords and make the partner column harmless: staff.password_teks is emptied, orders.ditanggung_mitra gets a default

Revision ID: g0k1c3e5f659
Revises: f8j0b2d4e548
Create Date: 2026-11-02 20:00:00.000000

Passwords were also kept as readable text next to their bcrypt hash (staff.password_teks) and shown to admins. The code no longer writes or
reads that column, so every stored value is erased here. The column itself goes in a later release (expand -> migrate -> contract): the
version still serving while this runs reads it.

The partner (mitra) program is gone from the code. orders.ditanggung_mitra stays NOT NULL on a database that has it, and the new code no longer
supplies it, so it gets a default of 0 now; the column and the leftover partner tables are dropped later, after their figures are archived.

Both steps look for the column first: a database built from the base revisions never had either of them. No row is added or removed.
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'g0k1c3e5f659'
down_revision: Union[str, Sequence[str], None] = 'f8j0b2d4e548'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ERASE_PASSWORDS = """
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'staff' AND column_name = 'password_teks') THEN
        UPDATE staff SET password_teks = NULL WHERE password_teks IS NOT NULL;
    END IF;
END $$
"""

PARTNER_DEFAULT = """
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'orders' AND column_name = 'ditanggung_mitra') THEN
        ALTER TABLE orders ALTER COLUMN ditanggung_mitra SET DEFAULT 0;
    END IF;
END $$
"""


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '1s'")
    op.execute(ERASE_PASSWORDS)
    op.execute(PARTNER_DEFAULT)


def downgrade() -> None:
    # The erased passwords cannot be restored, and should not be; the default is harmless where it stays.
    pass
