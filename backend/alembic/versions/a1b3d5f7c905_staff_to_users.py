"""akun karyawan berganti nama menjadi users: tabel, kolom staff_id, nama constraint dan indeks, dan fungsi yang menulis kolom itu

Revision ID: a1b3d5f7c905
Revises: a1b3d5f7c904
Create Date: 2026-11-25 10:00:00.000000

Hanya mengganti nama, tidak memindah baris; jumlah baris dan uang tidak berubah.
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'a1b3d5f7c905'
down_revision: Union[str, Sequence[str], None] = 'a1b3d5f7c904'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")

# Dibaca app/core/migration_check.py, supaya penjaga deploy mencocokkan jumlah baris tabel yang berganti nama.
TABLES = {'staff': 'users', 'outlet_batch_staff': 'outlet_batch_users', 'station_staff_stats': 'station_user_stats'}

# (lama, baru) berurutan: tabel bernama majemuk lebih dulu, lalu kolom, lalu sisa kata yang menunjuk tabel itu sendiri.
FORWARD = (
    ('outlet_batch_staff', 'outlet_batch_users'),
    ('station_staff_stats', 'station_user_stats'),
    ('staff_id', 'user_id'),
    ('staff', 'users'),
)
BACKWARD = (
    ('outlet_batch_users', 'outlet_batch_staff'),
    ('station_user_stats', 'station_staff_stats'),
    ('user_id', 'staff_id'),
    ('users', 'staff'),
)


def _renamed(name_expression: str, pairs: tuple[tuple[str, str], ...]) -> str:
    """Ekspresi SQL yang menerapkan semua pasangan berurutan pada [name_expression]."""
    expression = name_expression
    for old, new in pairs:
        expression = f"replace({expression}, '{old}', '{new}')"
    return expression


def _rename_all(pairs: tuple[tuple[str, str], ...], marker: str) -> str:
    """Satu blok atomik: kolom, tabel, constraint, indeks, lalu badan fungsi yang menulis kolom itu."""
    old_column, new_column = next((old, new) for old, new in pairs if old.endswith('_id'))
    return f"""
    DO $$
    DECLARE
        item record;
    BEGIN
        FOR item IN SELECT table_name FROM information_schema.columns
                    WHERE table_schema = 'public' AND column_name = '{old_column}' ORDER BY table_name LOOP
            EXECUTE format('ALTER TABLE %I RENAME COLUMN {old_column} TO {new_column}', item.table_name);
        END LOOP;
        FOR item IN SELECT tablename AS name FROM pg_tables
                    WHERE schemaname = 'public' AND tablename IN ({", ".join(f"'{old}'" for old, _ in pairs if old != old_column)}) ORDER BY tablename LOOP
            IF {_renamed('item.name', pairs)} <> item.name THEN
                EXECUTE format('ALTER TABLE %I RENAME TO %I', item.name, {_renamed('item.name', pairs)});
            END IF;
        END LOOP;
        FOR item IN SELECT c.conname AS name, t.relname AS owner FROM pg_constraint c
                    JOIN pg_class t ON t.oid = c.conrelid JOIN pg_namespace n ON n.oid = t.relnamespace
                    WHERE n.nspname = 'public' AND c.conname LIKE '%{marker}%' ORDER BY c.conname LOOP
            -- Nama yang hanya kebetulan memuat penanda (misalnya username) tidak berubah dan dilewati.
            IF {_renamed('item.name', pairs)} <> item.name THEN
                EXECUTE format('ALTER TABLE %I RENAME CONSTRAINT %I TO %I', item.owner, item.name, {_renamed('item.name', pairs)});
            END IF;
        END LOOP;
        FOR item IN SELECT indexname AS name FROM pg_indexes i
                    WHERE schemaname = 'public' AND indexname LIKE '%{marker}%'
                      AND NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = i.indexname) ORDER BY indexname LOOP
            IF {_renamed('item.name', pairs)} <> item.name THEN
                EXECUTE format('ALTER INDEX %I RENAME TO %I', item.name, {_renamed('item.name', pairs)});
            END IF;
        END LOOP;
        FOR item IN SELECT p.oid FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
                    WHERE n.nspname = 'public' AND p.prosrc LIKE '%{old_column}%' LOOP
            EXECUTE replace(pg_get_functiondef(item.oid), '{old_column}', '{new_column}');
        END LOOP;
    END $$;
    """


TARGET_CHECK = 'check_outlet_batches_target_values'


def _target(old: str, new: str) -> tuple[str, ...]:
    """Nilai tersimpan target tugas rutin ikut berganti; CHECK diganti dulu tanpa validasi, data diperbarui, lalu divalidasi."""
    return (
        f'ALTER TABLE outlet_batches DROP CONSTRAINT IF EXISTS {TARGET_CHECK}',
        f"UPDATE outlet_batches SET target = '{new}' WHERE target = '{old}'",
        f"ALTER TABLE outlet_batches ADD CONSTRAINT {TARGET_CHECK} CHECK (target IN ('shift', '{new}') AND (kind = 'routine' OR target = 'shift')) NOT VALID",
        f'ALTER TABLE outlet_batches VALIDATE CONSTRAINT {TARGET_CHECK}',
    )


def upgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    op.execute(_rename_all(FORWARD, 'staff'))
    for statement in _target('staff', 'users'):
        op.execute(statement)


def downgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    for statement in _target('users', 'staff'):
        op.execute(statement)
    op.execute(_rename_all(BACKWARD, 'user'))
