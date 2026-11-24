"""rilis Oktober 2026: indeks promo, hapus lunak akun, saldo stok, indeks catatan pesanan, hari bisnis, jejak uang, stasiun v2, tanda baca pembaruan, stasiun peran, dan daftar pesanan sesi

Revision ID: c3e5a7b9d104
Revises: a1b3c5d7e902
Create Date: 2026-10-27 20:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'c3e5a7b9d104'
down_revision: Union[str, Sequence[str], None] = 'a1b3c5d7e902'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Batas waktu dipasang di awal berkas; bagian berikutnya bergantung pada bagian sebelumnya, jadi urutannya tidak boleh diubah.
TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")


# Indeks promo: yang sedang berlaku (dialog koreksi, kasir) dan yang terbaru dulu (daftar Promosi berhalaman).
# (indeks, tabel, kolom, kondisi)
PROMO_INDEXES = (
    ('ix_promo_diskon_berlaku', 'promo_diskon', 'tanggal_selesai, tanggal_mulai', 'WHERE aktif'),
    ('ix_promo_diskon_created', 'promo_diskon', 'created_at DESC, id', ''),
    ('ix_promosi_cafe_created', 'promosi_cafe', 'created_at DESC, id', ''),
)


def _promo_indexes_upgrade() -> None:
    # IF NOT EXISTS: dijalankan dua kali atau pada database yang sudah punya indeksnya tidak mengubah apa pun.
    for name, table, columns, condition in PROMO_INDEXES:
        op.execute(f'CREATE INDEX IF NOT EXISTS {name} ON {table} ({columns}) {condition}'.strip())


def _promo_indexes_downgrade() -> None:
    for name, _table, _columns, _condition in PROMO_INDEXES:
        op.execute(f'DROP INDEX IF EXISTS {name}')


# Hapus lunak akun: baris tetap ada sehingga penjualan, sesi, pengeluaran, dan absen atas namanya tetap utuh, dan perannya dilepas lewat SET NULL.
STAFF_ROLE_FOREIGN_KEY = 'staff_role_id_fkey'
# Database lama menamai constraint ini sendiri, jadi dicari dari kolomnya, bukan dari nama.
STAFF_DROP_ROLE_FOREIGN_KEY = """
DO $$
DECLARE found text;
BEGIN
    FOR found IN
        SELECT c.conname FROM pg_constraint c
        JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY (c.conkey)
        WHERE c.conrelid = 'staff'::regclass AND c.contype = 'f' AND a.attname = 'role_id'
    LOOP
        EXECUTE format('ALTER TABLE staff DROP CONSTRAINT %I', found);
    END LOOP;
END $$;
"""


def _staff_soft_delete_upgrade() -> None:
    # Setiap langkah aman diulang dan tidak mengubah apa pun pada kali kedua.
    op.execute('ALTER TABLE staff ADD COLUMN IF NOT EXISTS dihapus_pada TIMESTAMPTZ NULL')
    op.execute('ALTER TABLE staff ALTER COLUMN role_id DROP NOT NULL')
    op.execute(STAFF_DROP_ROLE_FOREIGN_KEY)
    op.execute(f'ALTER TABLE staff ADD CONSTRAINT {STAFF_ROLE_FOREIGN_KEY} FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE SET NULL')


def _staff_soft_delete_downgrade() -> None:
    op.execute(STAFF_DROP_ROLE_FOREIGN_KEY)
    op.execute(f'ALTER TABLE staff ADD CONSTRAINT {STAFF_ROLE_FOREIGN_KEY} FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE RESTRICT')
    # Kembali wajib hanya bila tidak ada akun terhapus yang melepas perannya; selain itu tetap opsional, bukan gagal.
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM staff WHERE role_id IS NULL) THEN ALTER TABLE staff ALTER COLUMN role_id SET NOT NULL; END IF; END $$;")
    # Dipertahankan selama ada akun bertanda terhapus, supaya mundur tidak memunculkan lagi akun terhapus di daftar.
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM staff WHERE dihapus_pada IS NOT NULL) THEN ALTER TABLE staff DROP COLUMN IF EXISTS dihapus_pada; END IF; END $$;")


# Saldo bahan.saldo dan stok_item.saldo disimpan di baris dan digerakkan trigger setiap kartu ditulis, lalu dicocokkan dengan jumlah kartunya sebelum selesai.
BALANCE_INDEXES = (
    ('ix_kartu_bahan_outlet_created', 'kartu_bahan', 'outlet_id, created_at'),
    ('ix_kartu_stok_outlet_created', 'kartu_stok', 'outlet_id, created_at'),
)

BALANCE_INGREDIENT_CARD_FUNCTION = """
CREATE OR REPLACE FUNCTION kartu_bahan_saldo() RETURNS trigger AS $$
BEGIN
    IF TG_OP IN ('UPDATE', 'DELETE') AND OLD.bahan_id IS NOT NULL THEN
        UPDATE bahan SET saldo = saldo - OLD.qty WHERE id = OLD.bahan_id;
    END IF;
    IF TG_OP IN ('INSERT', 'UPDATE') AND NEW.bahan_id IS NOT NULL THEN
        UPDATE bahan SET saldo = saldo + NEW.qty WHERE id = NEW.bahan_id;
    END IF;
    RETURN NULL;
END $$ LANGUAGE plpgsql;
"""

BALANCE_STOCK_CARD_FUNCTION = """
CREATE OR REPLACE FUNCTION kartu_stok_saldo() RETURNS trigger AS $$
BEGIN
    IF TG_OP IN ('UPDATE', 'DELETE') AND OLD.menu_item_id IS NOT NULL THEN
        UPDATE stok_item SET saldo = saldo - OLD.qty WHERE outlet_id = OLD.outlet_id AND menu_item_id = OLD.menu_item_id;
    END IF;
    IF TG_OP IN ('INSERT', 'UPDATE') AND NEW.menu_item_id IS NOT NULL THEN
        UPDATE stok_item SET saldo = saldo + NEW.qty WHERE outlet_id = NEW.outlet_id AND menu_item_id = NEW.menu_item_id;
    END IF;
    RETURN NULL;
END $$ LANGUAGE plpgsql;
"""

# Barang jual ulang yang baru dilacak belakangan sudah punya kartu, jadi saldonya dimulai dari kartu itu dan ikut pindah bila cabang atau menunya berubah.
BALANCE_STOCK_ITEM_FUNCTION = """
CREATE OR REPLACE FUNCTION stok_item_saldo_awal() RETURNS trigger AS $$
BEGIN
    NEW.saldo := COALESCE((SELECT sum(qty) FROM kartu_stok WHERE outlet_id = NEW.outlet_id AND menu_item_id = NEW.menu_item_id), 0);
    RETURN NEW;
END $$ LANGUAGE plpgsql;
"""

BALANCE_TRIGGERS = (
    ('kartu_bahan_saldo', 'kartu_bahan', 'AFTER INSERT OR DELETE OR UPDATE OF bahan_id, qty', 'kartu_bahan_saldo()'),
    ('kartu_stok_saldo', 'kartu_stok', 'AFTER INSERT OR DELETE OR UPDATE OF outlet_id, menu_item_id, qty', 'kartu_stok_saldo()'),
    ('stok_item_saldo_awal', 'stok_item', 'BEFORE INSERT OR UPDATE OF outlet_id, menu_item_id', 'stok_item_saldo_awal()'),
)

BALANCE_BACKFILL = (
    "UPDATE bahan b SET saldo = COALESCE((SELECT sum(qty) FROM kartu_bahan k WHERE k.bahan_id = b.id), 0)",
    "UPDATE stok_item i SET saldo = COALESCE((SELECT sum(qty) FROM kartu_stok k WHERE k.outlet_id = i.outlet_id AND k.menu_item_id = i.menu_item_id), 0)",
)

BALANCE_SELF_CHECK = """
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM bahan b
        WHERE b.saldo <> COALESCE((SELECT sum(qty) FROM kartu_bahan k WHERE k.bahan_id = b.id), 0)
    ) THEN
        RAISE EXCEPTION 'bahan.saldo does not match its cards';
    END IF;
    IF EXISTS (
        SELECT 1 FROM stok_item i
        WHERE i.saldo <> COALESCE((SELECT sum(qty) FROM kartu_stok k WHERE k.outlet_id = i.outlet_id AND k.menu_item_id = i.menu_item_id), 0)
    ) THEN
        RAISE EXCEPTION 'stok_item.saldo does not match its cards';
    END IF;
END $$;
"""


def _stock_balances_upgrade() -> None:
    # Setiap langkah aman diulang dan berakhir di keadaan yang sama.
    op.execute('ALTER TABLE bahan ADD COLUMN IF NOT EXISTS saldo NUMERIC(16, 3) NOT NULL DEFAULT 0')
    op.execute('ALTER TABLE stok_item ADD COLUMN IF NOT EXISTS saldo NUMERIC(16, 3) NOT NULL DEFAULT 0')
    for name, table, columns in BALANCE_INDEXES:
        op.execute(f'CREATE INDEX IF NOT EXISTS {name} ON {table} ({columns})')
    op.execute(BALANCE_INGREDIENT_CARD_FUNCTION)
    op.execute(BALANCE_STOCK_CARD_FUNCTION)
    op.execute(BALANCE_STOCK_ITEM_FUNCTION)
    for name, table, timing, function in BALANCE_TRIGGERS:
        op.execute(f'DROP TRIGGER IF EXISTS {name} ON {table}')
        op.execute(f'CREATE TRIGGER {name} {timing} ON {table} FOR EACH ROW EXECUTE FUNCTION {function}')
    for statement in BALANCE_BACKFILL:
        op.execute(statement)
    op.execute(BALANCE_SELF_CHECK)


def _stock_balances_downgrade() -> None:
    for name, table, _timing, _function in BALANCE_TRIGGERS:
        op.execute(f'DROP TRIGGER IF EXISTS {name} ON {table}')
    for function in ('kartu_bahan_saldo()', 'kartu_stok_saldo()', 'stok_item_saldo_awal()'):
        op.execute(f'DROP FUNCTION IF EXISTS {function}')
    for name, _table, _columns in BALANCE_INDEXES:
        op.execute(f'DROP INDEX IF EXISTS {name}')
    op.execute('ALTER TABLE stok_item DROP COLUMN IF EXISTS saldo')
    op.execute('ALTER TABLE bahan DROP COLUMN IF EXISTS saldo')


# Indeks pesanan per catatan pesanan, supaya menghapus catatan tidak membaca semua pesanan.
def _order_note_index_upgrade() -> None:
    # IF NOT EXISTS: dijalankan dua kali atau pada database yang sudah punya indeksnya tidak mengubah apa pun.
    op.execute('CREATE INDEX IF NOT EXISTS ix_orders_catatan ON orders (catatan_id)')


def _order_note_index_downgrade() -> None:
    op.execute('DROP INDEX IF EXISTS ix_orders_catatan')


# Hari bisnis disimpan di setiap baris uang dan stok oleh trigger: ikut hari sesinya, atau hari WIB waktunya sendiri bila tanpa sesi.
DAY_TABLES = ('shifts', 'orders', 'expenses', 'kelebihan_bayar', 'kartu_stok', 'kartu_bahan')

# Rambatan mencari baris lewat induknya, dan saldo satu bahan sebelum suatu hari hanya membaca kartunya sendiri.
DAY_PARENT_INDEXES = (('ix_kelebihan_bayar_order_id', 'kelebihan_bayar', 'order_id'),)
DAY_DAY_INDEXES = (('ix_kartu_bahan_bahan_business_day', 'kartu_bahan', 'bahan_id, business_day'),)

DAY_WIB_DATE = """
CREATE OR REPLACE FUNCTION wib_date(instant timestamptz) RETURNS date AS $$
    SELECT ((instant AT TIME ZONE 'UTC') + interval '7 hours')::date
$$ LANGUAGE sql IMMUTABLE PARALLEL SAFE;
"""

DAY_SHIFT_DAY = """
CREATE OR REPLACE FUNCTION shifts_business_day() RETURNS trigger AS $$
BEGIN
    NEW.business_day := wib_date(NEW.start_time);
    RETURN NEW;
END $$ LANGUAGE plpgsql;
"""

# Baris yang sesinya sudah hilang mempertahankan harinya; hanya baris yang tidak pernah punya sesi memakai waktunya sendiri.
DAY_ORDER_DAY = """
CREATE OR REPLACE FUNCTION orders_business_day() RETURNS trigger AS $$
BEGIN
    NEW.business_day := COALESCE(
        (SELECT s.business_day FROM shifts s WHERE s.id = NEW.shift_id),
        CASE WHEN TG_OP = 'UPDATE' THEN OLD.business_day END,
        wib_date(NEW.created_at)
    );
    RETURN NEW;
END $$ LANGUAGE plpgsql;
"""

DAY_EXPENSE_DAY = """
CREATE OR REPLACE FUNCTION expenses_business_day() RETURNS trigger AS $$
BEGIN
    NEW.business_day := COALESCE(
        (SELECT s.business_day FROM shifts s WHERE s.id = NEW.shift_id),
        CASE WHEN TG_OP = 'UPDATE' THEN OLD.business_day END,
        wib_date(NEW.created_at)
    );
    RETURN NEW;
END $$ LANGUAGE plpgsql;
"""

DAY_OVERPAYMENT_DAY = """
CREATE OR REPLACE FUNCTION kelebihan_bayar_business_day() RETURNS trigger AS $$
BEGIN
    NEW.business_day := COALESCE(
        (SELECT o.business_day FROM orders o WHERE o.id = NEW.order_id),
        (SELECT s.business_day FROM shifts s WHERE s.id = NEW.shift_id),
        CASE WHEN TG_OP = 'UPDATE' THEN OLD.business_day END,
        wib_date(NEW.waktu)
    );
    RETURN NEW;
END $$ LANGUAGE plpgsql;
"""

DAY_STOCK_CARD_DAY = """
CREATE OR REPLACE FUNCTION kartu_stok_business_day() RETURNS trigger AS $$
BEGIN
    NEW.business_day := COALESCE(
        (SELECT o.business_day FROM orders o WHERE o.id = NEW.order_id),
        CASE WHEN TG_OP = 'UPDATE' THEN OLD.business_day END,
        wib_date(NEW.created_at)
    );
    RETURN NEW;
END $$ LANGUAGE plpgsql;
"""

DAY_INGREDIENT_CARD_DAY = """
CREATE OR REPLACE FUNCTION kartu_bahan_business_day() RETURNS trigger AS $$
BEGIN
    NEW.business_day := COALESCE(
        (SELECT o.business_day FROM orders o WHERE o.id = NEW.order_id),
        (SELECT e.business_day FROM expenses e WHERE e.id = NEW.expense_id),
        CASE WHEN TG_OP = 'UPDATE' THEN OLD.business_day END,
        wib_date(NEW.created_at)
    );
    RETURN NEW;
END $$ LANGUAGE plpgsql;
"""

# Menyentuh baris pewaris membuat triggernya sendiri membaca hari baru, sehingga aturannya tetap ditulis sekali per tabel.
DAY_SHIFT_CASCADE = """
CREATE OR REPLACE FUNCTION shifts_business_day_cascade() RETURNS trigger AS $$
BEGIN
    UPDATE orders SET business_day = NULL WHERE shift_id = NEW.id;
    UPDATE expenses SET business_day = NULL WHERE shift_id = NEW.id;
    RETURN NULL;
END $$ LANGUAGE plpgsql;
"""

DAY_ORDER_CASCADE = """
CREATE OR REPLACE FUNCTION orders_business_day_cascade() RETURNS trigger AS $$
BEGIN
    UPDATE kelebihan_bayar SET business_day = NULL WHERE order_id = NEW.id;
    UPDATE kartu_stok SET business_day = NULL WHERE order_id = NEW.id;
    UPDATE kartu_bahan SET business_day = NULL WHERE order_id = NEW.id;
    RETURN NULL;
END $$ LANGUAGE plpgsql;
"""

DAY_EXPENSE_CASCADE = """
CREATE OR REPLACE FUNCTION expenses_business_day_cascade() RETURNS trigger AS $$
BEGIN
    UPDATE kartu_bahan SET business_day = NULL WHERE expense_id = NEW.id AND order_id IS NULL;
    RETURN NULL;
END $$ LANGUAGE plpgsql;
"""

DAY_FUNCTIONS = (DAY_WIB_DATE, DAY_SHIFT_DAY, DAY_ORDER_DAY, DAY_EXPENSE_DAY, DAY_OVERPAYMENT_DAY, DAY_STOCK_CARD_DAY, DAY_INGREDIENT_CARD_DAY, DAY_SHIFT_CASCADE, DAY_ORDER_CASCADE, DAY_EXPENSE_CASCADE)

DAY_DAY_TRIGGERS = (
    ('shifts_business_day', 'shifts', 'BEFORE INSERT OR UPDATE', '', 'shifts_business_day()'),
    ('orders_business_day', 'orders', 'BEFORE INSERT OR UPDATE', '', 'orders_business_day()'),
    ('expenses_business_day', 'expenses', 'BEFORE INSERT OR UPDATE', '', 'expenses_business_day()'),
    ('kelebihan_bayar_business_day', 'kelebihan_bayar', 'BEFORE INSERT OR UPDATE', '', 'kelebihan_bayar_business_day()'),
    ('kartu_stok_business_day', 'kartu_stok', 'BEFORE INSERT OR UPDATE', '', 'kartu_stok_business_day()'),
    ('kartu_bahan_business_day', 'kartu_bahan', 'BEFORE INSERT OR UPDATE', '', 'kartu_bahan_business_day()'),
)

DAY_CASCADE_TRIGGERS = (
    ('shifts_business_day_cascade', 'shifts', 'AFTER UPDATE OF business_day', 'WHEN (OLD.business_day IS DISTINCT FROM NEW.business_day)', 'shifts_business_day_cascade()'),
    ('orders_business_day_cascade', 'orders', 'AFTER UPDATE OF business_day', 'WHEN (OLD.business_day IS DISTINCT FROM NEW.business_day)', 'orders_business_day_cascade()'),
    ('expenses_business_day_cascade', 'expenses', 'AFTER UPDATE OF business_day', 'WHEN (OLD.business_day IS DISTINCT FROM NEW.business_day)', 'expenses_business_day_cascade()'),
)

# Induk lebih dulu, supaya setiap baris pewaris membaca hari yang sudah terisi.
DAY_BACKFILL = (
    'UPDATE shifts SET business_day = wib_date(start_time)',
    'UPDATE orders o SET business_day = s.business_day FROM shifts s WHERE s.id = o.shift_id',
    'UPDATE orders SET business_day = wib_date(created_at) WHERE business_day IS NULL',
    'UPDATE expenses e SET business_day = s.business_day FROM shifts s WHERE s.id = e.shift_id',
    'UPDATE expenses SET business_day = wib_date(created_at) WHERE business_day IS NULL',
    'UPDATE kelebihan_bayar k SET business_day = o.business_day FROM orders o WHERE o.id = k.order_id',
    'UPDATE kelebihan_bayar k SET business_day = s.business_day FROM shifts s WHERE s.id = k.shift_id AND k.business_day IS NULL',
    'UPDATE kelebihan_bayar SET business_day = wib_date(waktu) WHERE business_day IS NULL',
    'UPDATE kartu_stok k SET business_day = o.business_day FROM orders o WHERE o.id = k.order_id',
    'UPDATE kartu_stok SET business_day = wib_date(created_at) WHERE business_day IS NULL',
    'UPDATE kartu_bahan k SET business_day = o.business_day FROM orders o WHERE o.id = k.order_id',
    'UPDATE kartu_bahan k SET business_day = e.business_day FROM expenses e WHERE e.id = k.expense_id AND k.business_day IS NULL',
    'UPDATE kartu_bahan SET business_day = wib_date(created_at) WHERE business_day IS NULL',
)

DAY_SELF_CHECK = """
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM shifts WHERE business_day IS DISTINCT FROM wib_date(start_time)) THEN
        RAISE EXCEPTION 'shifts.business_day does not follow start_time';
    END IF;
    IF EXISTS (SELECT 1 FROM orders o JOIN shifts s ON s.id = o.shift_id WHERE o.business_day IS DISTINCT FROM s.business_day) THEN
        RAISE EXCEPTION 'orders.business_day does not follow its session';
    END IF;
    IF EXISTS (SELECT 1 FROM expenses e JOIN shifts s ON s.id = e.shift_id WHERE e.business_day IS DISTINCT FROM s.business_day) THEN
        RAISE EXCEPTION 'expenses.business_day does not follow its session';
    END IF;
    IF EXISTS (SELECT 1 FROM kelebihan_bayar k JOIN orders o ON o.id = k.order_id WHERE k.business_day IS DISTINCT FROM o.business_day) THEN
        RAISE EXCEPTION 'kelebihan_bayar.business_day does not follow its order';
    END IF;
    IF EXISTS (SELECT 1 FROM kartu_stok k JOIN orders o ON o.id = k.order_id WHERE k.business_day IS DISTINCT FROM o.business_day) THEN
        RAISE EXCEPTION 'kartu_stok.business_day does not follow its order';
    END IF;
    IF EXISTS (SELECT 1 FROM kartu_bahan k JOIN orders o ON o.id = k.order_id WHERE k.business_day IS DISTINCT FROM o.business_day) THEN
        RAISE EXCEPTION 'kartu_bahan.business_day does not follow its order';
    END IF;
    IF EXISTS (
        SELECT 1 FROM kartu_bahan k JOIN expenses e ON e.id = k.expense_id
        WHERE k.order_id IS NULL AND k.business_day IS DISTINCT FROM e.business_day
    ) THEN
        RAISE EXCEPTION 'kartu_bahan.business_day does not follow its expense';
    END IF;
END $$;
"""


def _business_day_upgrade() -> None:
    # Rambatan dibuat setelah pengisian data lama supaya setiap baris hanya tersentuh sekali.
    for table in DAY_TABLES:
        op.execute(f'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS business_day DATE')
    for name, table, columns in DAY_PARENT_INDEXES:
        op.execute(f'CREATE INDEX IF NOT EXISTS {name} ON {table} ({columns})')
    for function in DAY_FUNCTIONS:
        op.execute(function)
    for name, table, timing, condition, function in (*DAY_DAY_TRIGGERS, *DAY_CASCADE_TRIGGERS):
        op.execute(f'DROP TRIGGER IF EXISTS {name} ON {table}')
    for name, table, timing, condition, function in DAY_DAY_TRIGGERS:
        op.execute(f'CREATE TRIGGER {name} {timing} ON {table} FOR EACH ROW {condition} EXECUTE FUNCTION {function}')
    for statement in DAY_BACKFILL:
        op.execute(statement)
    for name, table, timing, condition, function in DAY_CASCADE_TRIGGERS:
        op.execute(f'CREATE TRIGGER {name} {timing} ON {table} FOR EACH ROW {condition} EXECUTE FUNCTION {function}')
    op.execute(DAY_SELF_CHECK)
    for table in DAY_TABLES:
        op.execute(f'ALTER TABLE {table} ALTER COLUMN business_day SET NOT NULL')
        op.execute(f'CREATE INDEX IF NOT EXISTS ix_{table}_business_day ON {table} (business_day, outlet_id)')
    for name, table, columns in DAY_DAY_INDEXES:
        op.execute(f'CREATE INDEX IF NOT EXISTS {name} ON {table} ({columns})')


def _business_day_downgrade() -> None:
    for name, table, _timing, _condition, _function in (*DAY_CASCADE_TRIGGERS, *DAY_DAY_TRIGGERS):
        op.execute(f'DROP TRIGGER IF EXISTS {name} ON {table}')
    for function in (
        'shifts_business_day_cascade()',
        'orders_business_day_cascade()',
        'expenses_business_day_cascade()',
        'shifts_business_day()',
        'orders_business_day()',
        'expenses_business_day()',
        'kelebihan_bayar_business_day()',
        'kartu_stok_business_day()',
        'kartu_bahan_business_day()',
        'wib_date(timestamptz)',
    ):
        op.execute(f'DROP FUNCTION IF EXISTS {function}')
    for name, _table, _columns in DAY_DAY_INDEXES:
        op.execute(f'DROP INDEX IF EXISTS {name}')
    for table in DAY_TABLES:
        op.execute(f'DROP INDEX IF EXISTS ix_{table}_business_day')
        op.execute(f'ALTER TABLE {table} DROP COLUMN IF EXISTS business_day')
    for name, _table, _columns in DAY_PARENT_INDEXES:
        op.execute(f'DROP INDEX IF EXISTS {name}')


# Jejak perubahan uang yang sudah tercatat, ditulis trigger untuk setiap aplikasi yang memakai database ini, sengaja tanpa foreign key.
MONEY_TABLE = """
CREATE TABLE IF NOT EXISTS money_changes (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    outlet_id TEXT NOT NULL,
    business_day DATE NOT NULL,
    subject TEXT NOT NULL CONSTRAINT money_changes_subject CHECK (subject IN ('order', 'expense', 'overpayment', 'session')),
    subject_id TEXT NOT NULL,
    session_id TEXT,
    subject_label TEXT NOT NULL DEFAULT '',
    action TEXT NOT NULL CONSTRAINT money_changes_action CHECK (action IN ('late', 'update', 'void', 'unvoid', 'delete', 'move_out', 'move_in')),
    amount_before NUMERIC(12, 2) NOT NULL,
    amount_after NUMERIC(12, 2) NOT NULL,
    fields TEXT[] NOT NULL DEFAULT '{}',
    staff_id TEXT,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""

MONEY_INDEXES = (
    ('ix_money_changes_business_day', 'business_day, outlet_id'),
    ('ix_money_changes_subject', 'subject, subject_id'),
    ('ix_money_changes_session', 'session_id'),
    ('ix_money_changes_changed_at', 'changed_at'),
)

MONEY_WRITER = """
CREATE OR REPLACE FUNCTION money_change_write(
    p_outlet TEXT, p_day DATE, p_subject TEXT, p_id TEXT, p_session TEXT, p_label TEXT, p_action TEXT, p_before NUMERIC, p_after NUMERIC, p_fields TEXT[]
) RETURNS void AS $$
    INSERT INTO money_changes (outlet_id, business_day, subject, subject_id, session_id, subject_label, action, amount_before, amount_after, fields, staff_id)
    VALUES (p_outlet, p_day, p_subject, p_id, p_session, COALESCE(p_label, ''), p_action, p_before, p_after, p_fields, NULLIF(current_setting('app.staff_id', true), ''))
$$ LANGUAGE sql;
"""

# Penjualan sesi malam setelah tengah malam tidak terlambat, karena terlambat berarti sesinya sudah ditutup, bukan hari kalender lebih awal.
MONEY_LATE = """
CREATE OR REPLACE FUNCTION money_change_late(p_shift TEXT, p_day DATE) RETURNS boolean AS $$
    SELECT CASE
        WHEN p_shift IS NULL THEN p_day < wib_date(now())
        ELSE COALESCE((SELECT s.status = 'CLOSED' FROM shifts s WHERE s.id = p_shift), p_day < wib_date(now()))
    END
$$ LANGUAGE sql STABLE;
"""

# Baris yang disisipkan transaksi berjalan dicatat di setelan lokal transaksi, yang ikut berakhir bersama transaksinya.
MONEY_MARK = """
CREATE OR REPLACE FUNCTION money_change_mark() RETURNS trigger AS $$
BEGIN
    PERFORM set_config('money.fresh', COALESCE(current_setting('money.fresh', true), '') || ',' || TG_TABLE_NAME || ':' || NEW.id, true);
    RETURN NULL;
END $$ LANGUAGE plpgsql;
"""

MONEY_FRESH = """
CREATE OR REPLACE FUNCTION money_change_fresh(p_table TEXT, p_id TEXT) RETURNS boolean AS $$
    SELECT position(',' || p_table || ':' || p_id || ',' IN COALESCE(current_setting('money.fresh', true), '') || ',') > 0
$$ LANGUAGE sql STABLE;
"""

MONEY_COMPARE = """
CREATE OR REPLACE FUNCTION money_change_compare(
    p_subject TEXT, p_id TEXT, p_session TEXT, p_label TEXT,
    p_old_outlet TEXT, p_old_day DATE, p_old_amount NUMERIC,
    p_new_outlet TEXT, p_new_day DATE, p_new_amount NUMERIC,
    p_action TEXT, p_fields TEXT[]
) RETURNS void AS $$
BEGIN
    IF cardinality(p_fields) = 0 THEN
        RETURN;
    END IF;
    IF p_old_outlet IS DISTINCT FROM p_new_outlet OR p_old_day IS DISTINCT FROM p_new_day THEN
        PERFORM money_change_write(p_old_outlet, p_old_day, p_subject, p_id, p_session, p_label, 'move_out', p_old_amount, 0, p_fields);
        PERFORM money_change_write(p_new_outlet, p_new_day, p_subject, p_id, p_session, p_label, 'move_in', 0, p_new_amount, p_fields);
    ELSE
        PERFORM money_change_write(p_new_outlet, p_new_day, p_subject, p_id, p_session, p_label, p_action, p_old_amount, p_new_amount, p_fields);
    END IF;
END $$ LANGUAGE plpgsql;
"""

MONEY_ORDER_LATE = """
CREATE OR REPLACE FUNCTION orders_money_late() RETURNS trigger AS $$
DECLARE
    row orders%ROWTYPE;
BEGIN
    SELECT * INTO row FROM orders WHERE id = NEW.id;
    IF FOUND AND money_change_late(row.shift_id, row.business_day) THEN
        PERFORM money_change_write(row.outlet_id, row.business_day, 'order', row.id, row.shift_id, row.nomor_nota, 'late', 0,
            CASE WHEN row.voided_at IS NULL THEN row.total ELSE 0 END, ARRAY['total']);
    END IF;
    RETURN NULL;
END $$ LANGUAGE plpgsql;
"""

MONEY_ORDER_CHANGE = """
CREATE OR REPLACE FUNCTION orders_money_change() RETURNS trigger AS $$
DECLARE
    changed TEXT[] := '{}';
    old_amount NUMERIC;
    new_amount NUMERIC;
    verb TEXT := 'update';
BEGIN
    IF money_change_fresh(TG_TABLE_NAME, OLD.id) THEN
        RETURN NULL;
    END IF;
    old_amount := CASE WHEN OLD.voided_at IS NULL THEN OLD.total ELSE 0 END;
    IF TG_OP = 'DELETE' THEN
        PERFORM money_change_write(OLD.outlet_id, OLD.business_day, 'order', OLD.id, OLD.shift_id, OLD.nomor_nota, 'delete', old_amount, 0, ARRAY['total']);
        RETURN NULL;
    END IF;
    new_amount := CASE WHEN NEW.voided_at IS NULL THEN NEW.total ELSE 0 END;
    IF OLD.total IS DISTINCT FROM NEW.total THEN changed := array_append(changed, 'total'::text); END IF;
    IF OLD.voided_at IS DISTINCT FROM NEW.voided_at THEN
        changed := array_append(changed, 'void'::text);
        verb := CASE WHEN NEW.voided_at IS NULL THEN 'unvoid' ELSE 'void' END;
    END IF;
    IF OLD.payment_method IS DISTINCT FROM NEW.payment_method THEN changed := array_append(changed, 'payment_method'::text); END IF;
    IF OLD.outlet_id IS DISTINCT FROM NEW.outlet_id THEN changed := array_append(changed, 'outlet'::text); END IF;
    IF OLD.business_day IS DISTINCT FROM NEW.business_day THEN changed := array_append(changed, 'business_day'::text); END IF;
    PERFORM money_change_compare('order', NEW.id, NEW.shift_id, NEW.nomor_nota, OLD.outlet_id, OLD.business_day, old_amount,
        NEW.outlet_id, NEW.business_day, new_amount, verb, changed);
    RETURN NULL;
END $$ LANGUAGE plpgsql;
"""

MONEY_EXPENSE_LATE = """
CREATE OR REPLACE FUNCTION expenses_money_late() RETURNS trigger AS $$
DECLARE
    row expenses%ROWTYPE;
BEGIN
    SELECT * INTO row FROM expenses WHERE id = NEW.id;
    IF FOUND AND money_change_late(row.shift_id, row.business_day) THEN
        PERFORM money_change_write(row.outlet_id, row.business_day, 'expense', row.id, row.shift_id, row.nama_item, 'late', 0, row.jumlah, ARRAY['amount']);
    END IF;
    RETURN NULL;
END $$ LANGUAGE plpgsql;
"""

MONEY_EXPENSE_CHANGE = """
CREATE OR REPLACE FUNCTION expenses_money_change() RETURNS trigger AS $$
DECLARE
    changed TEXT[] := '{}';
BEGIN
    IF money_change_fresh(TG_TABLE_NAME, OLD.id) THEN
        RETURN NULL;
    END IF;
    IF TG_OP = 'DELETE' THEN
        PERFORM money_change_write(OLD.outlet_id, OLD.business_day, 'expense', OLD.id, OLD.shift_id, OLD.nama_item, 'delete', OLD.jumlah, 0, ARRAY['amount']);
        RETURN NULL;
    END IF;
    IF OLD.jumlah IS DISTINCT FROM NEW.jumlah THEN changed := array_append(changed, 'amount'::text); END IF;
    IF OLD.sumber_dana IS DISTINCT FROM NEW.sumber_dana THEN changed := array_append(changed, 'fund_source'::text); END IF;
    IF OLD.outlet_id IS DISTINCT FROM NEW.outlet_id THEN changed := array_append(changed, 'outlet'::text); END IF;
    IF OLD.business_day IS DISTINCT FROM NEW.business_day THEN changed := array_append(changed, 'business_day'::text); END IF;
    PERFORM money_change_compare('expense', NEW.id, COALESCE(NEW.shift_id, OLD.shift_id), NEW.nama_item, OLD.outlet_id, OLD.business_day, OLD.jumlah,
        NEW.outlet_id, NEW.business_day, NEW.jumlah, 'update', changed);
    RETURN NULL;
END $$ LANGUAGE plpgsql;
"""

MONEY_OVERPAYMENT_LATE = """
CREATE OR REPLACE FUNCTION kelebihan_bayar_money_late() RETURNS trigger AS $$
DECLARE
    row kelebihan_bayar%ROWTYPE;
BEGIN
    SELECT * INTO row FROM kelebihan_bayar WHERE id = NEW.id;
    IF FOUND AND money_change_late(row.shift_id, row.business_day) THEN
        PERFORM money_change_write(row.outlet_id, row.business_day, 'overpayment', row.id, row.shift_id, row.metode_label, 'late', 0, row.jumlah, ARRAY['amount']);
    END IF;
    RETURN NULL;
END $$ LANGUAGE plpgsql;
"""

MONEY_OVERPAYMENT_CHANGE = """
CREATE OR REPLACE FUNCTION kelebihan_bayar_money_change() RETURNS trigger AS $$
DECLARE
    changed TEXT[] := '{}';
BEGIN
    IF money_change_fresh(TG_TABLE_NAME, OLD.id) THEN
        RETURN NULL;
    END IF;
    IF TG_OP = 'DELETE' THEN
        PERFORM money_change_write(OLD.outlet_id, OLD.business_day, 'overpayment', OLD.id, OLD.shift_id, OLD.metode_label, 'delete', OLD.jumlah, 0, ARRAY['amount']);
        RETURN NULL;
    END IF;
    IF OLD.jumlah IS DISTINCT FROM NEW.jumlah THEN changed := array_append(changed, 'amount'::text); END IF;
    IF OLD.outlet_id IS DISTINCT FROM NEW.outlet_id THEN changed := array_append(changed, 'outlet'::text); END IF;
    IF OLD.business_day IS DISTINCT FROM NEW.business_day THEN changed := array_append(changed, 'business_day'::text); END IF;
    PERFORM money_change_compare('overpayment', NEW.id, NEW.shift_id, NEW.metode_label, OLD.outlet_id, OLD.business_day, OLD.jumlah,
        NEW.outlet_id, NEW.business_day, NEW.jumlah, 'update', changed);
    RETURN NULL;
END $$ LANGUAGE plpgsql;
"""

# Uang milik sesi adalah hasil hitung laci setelah ditutup; penjualan dan pengeluarannya dicatat di barisnya sendiri.
MONEY_SESSION_CHANGE = """
CREATE OR REPLACE FUNCTION shifts_money_change() RETURNS trigger AS $$
DECLARE
    changed TEXT[] := '{}';
BEGIN
    IF TG_OP = 'DELETE' THEN
        PERFORM money_change_write(OLD.outlet_id, OLD.business_day, 'session', OLD.id, OLD.id, OLD.kode_shift, 'delete', COALESCE(OLD.uang_aktual, 0), 0, ARRAY['actual_cash']);
        RETURN NULL;
    END IF;
    IF OLD.status IS DISTINCT FROM 'CLOSED' THEN
        RETURN NULL;
    END IF;
    IF OLD.modal_awal IS DISTINCT FROM NEW.modal_awal THEN changed := array_append(changed, 'opening_cash'::text); END IF;
    IF OLD.uang_aktual IS DISTINCT FROM NEW.uang_aktual THEN changed := array_append(changed, 'actual_cash'::text); END IF;
    IF OLD.selisih IS DISTINCT FROM NEW.selisih THEN changed := array_append(changed, 'difference'::text); END IF;
    IF OLD.outlet_id IS DISTINCT FROM NEW.outlet_id THEN changed := array_append(changed, 'outlet'::text); END IF;
    IF OLD.business_day IS DISTINCT FROM NEW.business_day THEN changed := array_append(changed, 'business_day'::text); END IF;
    PERFORM money_change_compare('session', NEW.id, NEW.id, NEW.kode_shift, OLD.outlet_id, OLD.business_day, COALESCE(OLD.uang_aktual, 0),
        NEW.outlet_id, NEW.business_day, COALESCE(NEW.uang_aktual, 0), 'update', changed);
    RETURN NULL;
END $$ LANGUAGE plpgsql;
"""

MONEY_FUNCTIONS = (
    MONEY_WRITER, MONEY_LATE, MONEY_MARK, MONEY_FRESH, MONEY_COMPARE,
    MONEY_ORDER_LATE, MONEY_ORDER_CHANGE, MONEY_EXPENSE_LATE, MONEY_EXPENSE_CHANGE, MONEY_OVERPAYMENT_LATE, MONEY_OVERPAYMENT_CHANGE, MONEY_SESSION_CHANGE,
)

MONEY_MARK_TRIGGERS = (
    ('orders_money_mark', 'orders'),
    ('expenses_money_mark', 'expenses'),
    ('kelebihan_bayar_money_mark', 'kelebihan_bayar'),
)

# Entri terlambat dibaca saat commit, sehingga jumlah yang diisi setelah insert yang tercatat.
MONEY_LATE_TRIGGERS = (
    ('orders_money_late', 'orders', 'orders_money_late()'),
    ('expenses_money_late', 'expenses', 'expenses_money_late()'),
    ('kelebihan_bayar_money_late', 'kelebihan_bayar', 'kelebihan_bayar_money_late()'),
)

MONEY_CHANGE_TRIGGERS = (
    ('orders_money_change', 'orders', 'orders_money_change()'),
    ('expenses_money_change', 'expenses', 'expenses_money_change()'),
    ('kelebihan_bayar_money_change', 'kelebihan_bayar', 'kelebihan_bayar_money_change()'),
    ('shifts_money_change', 'shifts', 'shifts_money_change()'),
)

MONEY_DROPPED_FUNCTIONS = (
    'orders_money_late()',
    'expenses_money_late()',
    'kelebihan_bayar_money_late()',
    'orders_money_change()',
    'expenses_money_change()',
    'kelebihan_bayar_money_change()',
    'shifts_money_change()',
    'money_change_compare(TEXT, TEXT, TEXT, TEXT, TEXT, DATE, NUMERIC, TEXT, DATE, NUMERIC, TEXT, TEXT[])',
    'money_change_fresh(TEXT, TEXT)',
    'money_change_mark()',
    'money_change_late(TEXT, DATE)',
    'money_change_write(TEXT, DATE, TEXT, TEXT, TEXT, TEXT, TEXT, NUMERIC, NUMERIC, TEXT[])',
)


def _money_changes_upgrade() -> None:
    # Setiap langkah aman diulang dan berakhir di keadaan yang sama.
    op.execute(MONEY_TABLE)
    for name, columns in MONEY_INDEXES:
        op.execute(f'CREATE INDEX IF NOT EXISTS {name} ON money_changes ({columns})')
    for function in MONEY_FUNCTIONS:
        op.execute(function)
    for name, table, function in (*MONEY_LATE_TRIGGERS, *MONEY_CHANGE_TRIGGERS):
        op.execute(f'DROP TRIGGER IF EXISTS {name} ON {table}')
    for name, table in MONEY_MARK_TRIGGERS:
        op.execute(f'DROP TRIGGER IF EXISTS {name} ON {table}')
        op.execute(f'CREATE TRIGGER {name} AFTER INSERT ON {table} FOR EACH ROW EXECUTE FUNCTION money_change_mark()')
    for name, table, function in MONEY_LATE_TRIGGERS:
        op.execute(f'CREATE CONSTRAINT TRIGGER {name} AFTER INSERT ON {table} DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION {function}')
    for name, table, function in MONEY_CHANGE_TRIGGERS:
        op.execute(f'CREATE TRIGGER {name} AFTER UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION {function}')


def _money_changes_downgrade() -> None:
    for name, table, _function in (*MONEY_LATE_TRIGGERS, *MONEY_CHANGE_TRIGGERS):
        op.execute(f'DROP TRIGGER IF EXISTS {name} ON {table}')
    for name, table in MONEY_MARK_TRIGGERS:
        op.execute(f'DROP TRIGGER IF EXISTS {name} ON {table}')
    for function in MONEY_DROPPED_FUNCTIONS:
        op.execute(f'DROP FUNCTION IF EXISTS {function}')
    op.execute('DROP TABLE IF EXISTS money_changes')


# Stasiun v2: stasiun, pengaturan per cabang, tugas per tahap, riwayat langkah, dan ringkasan waktu.
STATION_TABLES = (
    """
    CREATE TABLE IF NOT EXISTS stations (
        id TEXT NOT NULL DEFAULT gen_random_uuid()::text,
        position INTEGER NOT NULL DEFAULT 0,
        target_seconds INTEGER,
        hold_for_food BOOLEAN NOT NULL DEFAULT false,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        name TEXT NOT NULL,
        kind TEXT NOT NULL,
        CONSTRAINT pk_stations PRIMARY KEY (id),
        CONSTRAINT check_stations_name_length CHECK (char_length(name) BETWEEN 1 AND 40),
        CONSTRAINT check_stations_kind_value CHECK (kind IN ('make', 'deliver', 'handover')),
        CONSTRAINT check_stations_target_seconds_range CHECK (target_seconds BETWEEN 1 AND 86400)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS station_flows (
        outlet_id TEXT NOT NULL,
        active BOOLEAN NOT NULL DEFAULT false,
        CONSTRAINT pk_station_flows PRIMARY KEY (outlet_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS station_branch_settings (
        outlet_id TEXT NOT NULL,
        station_id TEXT NOT NULL,
        target_seconds INTEGER,
        used BOOLEAN NOT NULL DEFAULT true,
        hold_for_food BOOLEAN,
        CONSTRAINT pk_station_branch_settings PRIMARY KEY (outlet_id, station_id),
        CONSTRAINT check_station_branch_settings_target_seconds_range CHECK (target_seconds BETWEEN 1 AND 86400)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS category_stations (
        category_id TEXT NOT NULL,
        station_id TEXT NOT NULL,
        CONSTRAINT pk_category_stations PRIMARY KEY (category_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS category_branch_stations (
        outlet_id TEXT NOT NULL,
        category_id TEXT NOT NULL,
        station_id TEXT,
        CONSTRAINT pk_category_branch_stations PRIMARY KEY (outlet_id, category_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS menu_targets (
        menu_item_id TEXT NOT NULL,
        target_seconds INTEGER NOT NULL,
        CONSTRAINT pk_menu_targets PRIMARY KEY (menu_item_id),
        CONSTRAINT check_menu_targets_target_seconds_range CHECK (target_seconds BETWEEN 1 AND 86400)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS menu_branch_targets (
        outlet_id TEXT NOT NULL,
        menu_item_id TEXT NOT NULL,
        target_seconds INTEGER NOT NULL,
        CONSTRAINT pk_menu_branch_targets PRIMARY KEY (outlet_id, menu_item_id),
        CONSTRAINT check_menu_branch_targets_target_seconds_range CHECK (target_seconds BETWEEN 1 AND 86400)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS station_tasks (
        id TEXT NOT NULL DEFAULT gen_random_uuid()::text,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        arrived_at TIMESTAMPTZ,
        started_at TIMESTAMPTZ,
        finished_at TIMESTAMPTZ,
        removed_at TIMESTAMPTZ,
        acknowledged_at TIMESTAMPTZ,
        version INTEGER NOT NULL DEFAULT 1,
        target_seconds INTEGER,
        order_id TEXT NOT NULL,
        outlet_id TEXT NOT NULL,
        station_id TEXT NOT NULL,
        order_item_id TEXT,
        started_by TEXT,
        finished_by TEXT,
        correction TEXT,
        removed_label TEXT,
        CONSTRAINT pk_station_tasks PRIMARY KEY (id),
        CONSTRAINT check_station_tasks_correction_value CHECK (correction IN ('added', 'changed')),
        CONSTRAINT check_station_tasks_removed_label_length CHECK (char_length(removed_label) <= 300),
        CONSTRAINT check_station_tasks_target_seconds_range CHECK (target_seconds BETWEEN 1 AND 86400),
        CONSTRAINT check_station_tasks_started_at_order CHECK (started_at IS NULL OR arrived_at IS NOT NULL),
        CONSTRAINT check_station_tasks_finished_at_order CHECK (finished_at IS NULL OR started_at IS NOT NULL)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS station_task_steps (
        id TEXT NOT NULL DEFAULT gen_random_uuid()::text,
        at TIMESTAMPTZ NOT NULL DEFAULT now(),
        intervened BOOLEAN NOT NULL DEFAULT false,
        task_id TEXT NOT NULL,
        staff_id TEXT,
        step TEXT NOT NULL,
        reason TEXT,
        CONSTRAINT pk_station_task_steps PRIMARY KEY (id),
        CONSTRAINT check_station_task_steps_step_value CHECK (step IN ('arrive', 'start', 'finish', 'undo', 'acknowledge')),
        CONSTRAINT check_station_task_steps_reason_length CHECK (char_length(reason) BETWEEN 1 AND 255),
        CONSTRAINT check_station_task_steps_reason_intervened CHECK (NOT intervened OR reason IS NOT NULL)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS station_staff_stats (
        id TEXT NOT NULL DEFAULT gen_random_uuid()::text,
        business_day DATE NOT NULL,
        wait_seconds BIGINT NOT NULL DEFAULT 0,
        work_seconds BIGINT NOT NULL DEFAULT 0,
        tasks INTEGER NOT NULL DEFAULT 0,
        targeted INTEGER NOT NULL DEFAULT 0,
        on_time INTEGER NOT NULL DEFAULT 0,
        hour SMALLINT NOT NULL,
        outlet_id TEXT NOT NULL,
        station_id TEXT NOT NULL,
        staff_id TEXT,
        CONSTRAINT pk_station_staff_stats PRIMARY KEY (id),
        CONSTRAINT check_station_staff_stats_hour_range CHECK (hour BETWEEN 0 AND 23)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS station_menu_stats (
        id TEXT NOT NULL DEFAULT gen_random_uuid()::text,
        business_day DATE NOT NULL,
        wait_seconds BIGINT NOT NULL DEFAULT 0,
        work_seconds BIGINT NOT NULL DEFAULT 0,
        tasks INTEGER NOT NULL DEFAULT 0,
        targeted INTEGER NOT NULL DEFAULT 0,
        on_time INTEGER NOT NULL DEFAULT 0,
        hour SMALLINT NOT NULL,
        outlet_id TEXT NOT NULL,
        station_id TEXT NOT NULL,
        menu_item_id TEXT,
        menu_name TEXT NOT NULL,
        CONSTRAINT pk_station_menu_stats PRIMARY KEY (id),
        CONSTRAINT check_station_menu_stats_hour_range CHECK (hour BETWEEN 0 AND 23),
        CONSTRAINT check_station_menu_stats_menu_name_length CHECK (char_length(menu_name) BETWEEN 1 AND 255)
    )
    """,
)

# Indeks penopang foreign key dibuat sebelum foreign key-nya (rules 4.4.1).
STATION_INDEXES = (
    "CREATE UNIQUE INDEX IF NOT EXISTS unique_stations_name ON stations (lower(name))",
    "CREATE UNIQUE INDEX IF NOT EXISTS unique_stations_kind ON stations (kind) WHERE kind <> 'make'",
    "CREATE INDEX IF NOT EXISTS index_station_branch_settings_on_station_id ON station_branch_settings (station_id)",
    "CREATE INDEX IF NOT EXISTS index_category_stations_on_station_id ON category_stations (station_id)",
    "CREATE INDEX IF NOT EXISTS index_category_branch_stations_on_category_id ON category_branch_stations (category_id)",
    "CREATE INDEX IF NOT EXISTS index_category_branch_stations_on_station_id ON category_branch_stations (station_id)",
    "CREATE INDEX IF NOT EXISTS index_menu_branch_targets_on_menu_item_id ON menu_branch_targets (menu_item_id)",
    "CREATE INDEX IF NOT EXISTS index_station_tasks_on_order_id ON station_tasks (order_id)",
    "CREATE INDEX IF NOT EXISTS index_station_tasks_on_order_item_id ON station_tasks (order_item_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS unique_station_tasks_order_item_id_station_id ON station_tasks (order_item_id, station_id) WHERE order_item_id IS NOT NULL",
    "CREATE INDEX IF NOT EXISTS index_station_tasks_on_outlet_id_and_finished_at ON station_tasks (outlet_id, finished_at)",
    "CREATE INDEX IF NOT EXISTS index_station_tasks_on_station_id ON station_tasks (station_id)",
    "CREATE INDEX IF NOT EXISTS index_station_tasks_on_started_by ON station_tasks (started_by)",
    "CREATE INDEX IF NOT EXISTS index_station_tasks_on_finished_by ON station_tasks (finished_by)",
    "CREATE INDEX IF NOT EXISTS index_station_task_steps_on_task_id ON station_task_steps (task_id)",
    "CREATE INDEX IF NOT EXISTS index_station_task_steps_on_staff_id ON station_task_steps (staff_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS unique_station_staff_stats_key ON station_staff_stats (outlet_id, business_day, hour, station_id, staff_id)",
    "CREATE INDEX IF NOT EXISTS index_station_staff_stats_on_station_id ON station_staff_stats (station_id)",
    "CREATE INDEX IF NOT EXISTS index_station_staff_stats_on_staff_id ON station_staff_stats (staff_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS unique_station_menu_stats_key ON station_menu_stats (outlet_id, business_day, hour, station_id, menu_item_id)",
    "CREATE INDEX IF NOT EXISTS index_station_menu_stats_on_station_id ON station_menu_stats (station_id)",
    "CREATE INDEX IF NOT EXISTS index_station_menu_stats_on_menu_item_id ON station_menu_stats (menu_item_id)",
)

# (tabel, nama, kolom, tujuan, aksi saat induk dihapus); dibuat NOT VALID lalu divalidasi terpisah (rules 4.12.3).
STATION_FOREIGN_KEYS = (
    ("station_flows", "fk_station_flows_outlet_id_outlets", "outlet_id", "outlets", "CASCADE"),
    ("station_branch_settings", "fk_station_branch_settings_outlet_id_outlets", "outlet_id", "outlets", "CASCADE"),
    ("station_branch_settings", "fk_station_branch_settings_station_id_stations", "station_id", "stations", "CASCADE"),
    ("category_stations", "fk_category_stations_category_id_kategori", "category_id", "kategori", "CASCADE"),
    ("category_stations", "fk_category_stations_station_id_stations", "station_id", "stations", "RESTRICT"),
    ("category_branch_stations", "fk_category_branch_stations_outlet_id_outlets", "outlet_id", "outlets", "CASCADE"),
    ("category_branch_stations", "fk_category_branch_stations_category_id_kategori", "category_id", "kategori", "CASCADE"),
    ("category_branch_stations", "fk_category_branch_stations_station_id_stations", "station_id", "stations", "RESTRICT"),
    ("menu_targets", "fk_menu_targets_menu_item_id_menu_items", "menu_item_id", "menu_items", "CASCADE"),
    ("menu_branch_targets", "fk_menu_branch_targets_outlet_id_outlets", "outlet_id", "outlets", "CASCADE"),
    ("menu_branch_targets", "fk_menu_branch_targets_menu_item_id_menu_items", "menu_item_id", "menu_items", "CASCADE"),
    ("station_tasks", "fk_station_tasks_order_id_orders", "order_id", "orders", "CASCADE"),
    ("station_tasks", "fk_station_tasks_order_item_id_order_items", "order_item_id", "order_items", "SET NULL"),
    ("station_tasks", "fk_station_tasks_outlet_id_outlets", "outlet_id", "outlets", "RESTRICT"),
    ("station_tasks", "fk_station_tasks_station_id_stations", "station_id", "stations", "RESTRICT"),
    ("station_tasks", "fk_station_tasks_started_by_staff", "started_by", "staff", "SET NULL"),
    ("station_tasks", "fk_station_tasks_finished_by_staff", "finished_by", "staff", "SET NULL"),
    ("station_task_steps", "fk_station_task_steps_task_id_station_tasks", "task_id", "station_tasks", "CASCADE"),
    ("station_task_steps", "fk_station_task_steps_staff_id_staff", "staff_id", "staff", "SET NULL"),
    ("station_staff_stats", "fk_station_staff_stats_outlet_id_outlets", "outlet_id", "outlets", "RESTRICT"),
    ("station_staff_stats", "fk_station_staff_stats_station_id_stations", "station_id", "stations", "RESTRICT"),
    ("station_staff_stats", "fk_station_staff_stats_staff_id_staff", "staff_id", "staff", "SET NULL"),
    ("station_menu_stats", "fk_station_menu_stats_outlet_id_outlets", "outlet_id", "outlets", "RESTRICT"),
    ("station_menu_stats", "fk_station_menu_stats_station_id_stations", "station_id", "stations", "RESTRICT"),
    ("station_menu_stats", "fk_station_menu_stats_menu_item_id_menu_items", "menu_item_id", "menu_items", "SET NULL"),
)

# Salinan pengaturan dari tabel lama, hanya bila tabel itu ada; jenis lama 'buat' dan 'antar' dipetakan ke nama baru.
STATION_BACKFILL = """
DO $$
BEGIN
    IF to_regclass('public.stasiun') IS NOT NULL THEN
        INSERT INTO stations (id, name, kind, position, created_at)
        SELECT id, left(nama, 40), CASE jenis WHEN 'antar' THEN 'deliver' ELSE 'make' END, urutan, created_at
        FROM stasiun
        ON CONFLICT DO NOTHING;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'kategori' AND column_name = 'stasiun_id') THEN
        INSERT INTO category_stations (category_id, station_id)
        SELECT k.id, k.stasiun_id FROM kategori k JOIN stations s ON s.id = k.stasiun_id AND s.kind = 'make'
        ON CONFLICT DO NOTHING;
    END IF;
END $$;
"""


def _station_foreign_key(table: str, name: str, column: str, target: str, action: str) -> str:
    return f"""
    DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '{name}') THEN
            ALTER TABLE {table} ADD CONSTRAINT {name} FOREIGN KEY ({column}) REFERENCES {target}(id) ON DELETE {action} NOT VALID;
        END IF;
    END $$;
    """


def _station_stages_upgrade() -> None:
    # Setiap langkah aman diulang dan berakhir di keadaan yang sama.
    for statement in (*STATION_TABLES, *STATION_INDEXES):
        op.execute(statement)
    for table, name, column, target, action in STATION_FOREIGN_KEYS:
        op.execute(_station_foreign_key(table, name, column, target, action))
    for table, name, _column, _target, _action in STATION_FOREIGN_KEYS:
        op.execute(f"ALTER TABLE {table} VALIDATE CONSTRAINT {name}")
    op.execute(STATION_BACKFILL)


def _station_stages_downgrade() -> None:
    for table in (
        "station_menu_stats",
        "station_staff_stats",
        "station_task_steps",
        "station_tasks",
        "menu_branch_targets",
        "menu_targets",
        "category_branch_stations",
        "category_stations",
        "station_branch_settings",
        "station_flows",
        "stations",
    ):
        op.execute(f"DROP TABLE IF EXISTS {table}")


# Versi ringkasan pembaruan terakhir yang sudah dibaca setiap akun, per sisi (web admin, PWA karyawan, tablet).
RELEASE_READS_TABLE = """
CREATE TABLE IF NOT EXISTS release_reads (
    read_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    staff_id TEXT NOT NULL,
    surface TEXT NOT NULL,
    version TEXT NOT NULL,
    CONSTRAINT pk_release_reads PRIMARY KEY (staff_id, surface),
    CONSTRAINT check_release_reads_surface_value CHECK (surface IN ('management', 'employee', 'operational')),
    CONSTRAINT check_release_reads_version_length CHECK (char_length(version) BETWEEN 1 AND 20)
)
"""

# CASCADE karena penanda ini bagian dari akunnya, dan backend lama masih menghapus staff secara permanen; kunci utama sudah diawali staff_id.
RELEASE_READS_FOREIGN_KEY = """
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_release_reads_staff_id_staff') THEN
        ALTER TABLE release_reads ADD CONSTRAINT fk_release_reads_staff_id_staff FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE CASCADE NOT VALID;
    END IF;
END $$;
"""


def _release_reads_upgrade() -> None:
    op.execute(RELEASE_READS_TABLE)
    op.execute(RELEASE_READS_FOREIGN_KEY)
    op.execute("ALTER TABLE release_reads VALIDATE CONSTRAINT fk_release_reads_staff_id_staff")


def _release_reads_downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS release_reads")


# Stasiun yang tampil di tablet untuk akun berperan ini; kosong berarti peran tanpa stasiun, dan menghapus stasiun hanya melepasnya.
ROLE_STATION_COLUMN = "ALTER TABLE roles ADD COLUMN IF NOT EXISTS station_id TEXT NULL"
ROLE_STATION_INDEX = "CREATE INDEX IF NOT EXISTS index_roles_on_station_id ON roles (station_id)"
ROLE_STATION_FOREIGN_KEY = """
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_roles_station_id_stations') THEN
        ALTER TABLE roles ADD CONSTRAINT fk_roles_station_id_stations FOREIGN KEY (station_id) REFERENCES stations(id) ON DELETE SET NULL NOT VALID;
    END IF;
END $$;
"""


def _role_station_upgrade() -> None:
    op.execute(ROLE_STATION_COLUMN)
    op.execute(ROLE_STATION_INDEX)
    op.execute(ROLE_STATION_FOREIGN_KEY)
    op.execute("ALTER TABLE roles VALIDATE CONSTRAINT fk_roles_station_id_stations")


def _role_station_downgrade() -> None:
    op.execute("ALTER TABLE roles DROP CONSTRAINT IF EXISTS fk_roles_station_id_stations")
    op.execute("DROP INDEX IF EXISTS index_roles_on_station_id")
    op.execute("ALTER TABLE roles DROP COLUMN IF EXISTS station_id")


# Daftar pesanan satu sesi, terbaru dulu dan berkursor; indeks lama per shift_id tercakup kolom depannya, jadi dihapus setelah penggantinya ada.
def _session_order_page_index_upgrade() -> None:
    op.execute("CREATE INDEX IF NOT EXISTS index_orders_on_shift_id_and_created_at_and_id ON orders (shift_id, created_at DESC, id DESC)")
    op.execute("DROP INDEX IF EXISTS ix_orders_shift_id")


def _session_order_page_index_downgrade() -> None:
    op.execute("CREATE INDEX IF NOT EXISTS ix_orders_shift_id ON orders (shift_id)")
    op.execute("DROP INDEX IF EXISTS index_orders_on_shift_id_and_created_at_and_id")


def upgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    _promo_indexes_upgrade()
    _staff_soft_delete_upgrade()
    _stock_balances_upgrade()
    _order_note_index_upgrade()
    _business_day_upgrade()
    _money_changes_upgrade()
    _station_stages_upgrade()
    _release_reads_upgrade()
    _role_station_upgrade()
    _session_order_page_index_upgrade()


def downgrade() -> None:
    _session_order_page_index_downgrade()
    _role_station_downgrade()
    _release_reads_downgrade()
    _station_stages_downgrade()
    _money_changes_downgrade()
    _business_day_downgrade()
    _order_note_index_downgrade()
    _stock_balances_downgrade()
    _staff_soft_delete_downgrade()
    _promo_indexes_downgrade()
