"""pelanggan terdaftar, kunjungan, dan benefit mitra kembali seperti FOMO v2: tabel customers, visits, partners, partner_employees, partner_employee_free_menus, benefit_usages, serta kolom orders.customer_id dan orders.partner_covered

Revision ID: b1e3a5c7d879
Revises: a9d1f3b5c768
Create Date: 2026-11-18 10:00:00.000000

Rancangan dan aturan ON DELETE mengikuti skema FOMO (diambil dari database hasil rantai lama dan rantai v2). Yang tidak dibawa: partner_admins dan
partner_invoices (portal kerja sama di luar v2), kolom visits.recognition_event_id tanpa kunci asing (kamera tidak ada di sini), dan tabel wajah.
Nama indeks dan constraint mengikuti pola tetap proyek. Semua langkah aman diulang; tabel baru kosong, jadi kunci asing langsung divalidasi.
Id mitra, karyawan mitra, menu gratis, dan pemakaian benefit bertipe teks seperti id tabel lain. Aturan ON DELETE ke pelanggan, mitra, dan pesanan menyimpang dari FOMO (semuanya RESTRICT); alasannya di komentar FOREIGN_KEYS.
Down tidak melakukan apa pun: membuangnya akan menghapus data pelanggan dan benefit, dan kesalahan setelah rilis diperbaiki dengan migrasi maju.
"""
from typing import Sequence, Union

from alembic import op

from app.core.search import trigram_opclass
from sqlalchemy import text

revision: str = 'b1e3a5c7d879'
down_revision: Union[str, Sequence[str], None] = 'a9d1f3b5c768'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")

TABLES = (
    """
    CREATE TABLE IF NOT EXISTS customers (
        id VARCHAR NOT NULL,
        name VARCHAR(255) NOT NULL,
        contact VARCHAR(255),
        notes TEXT,
        preferences TEXT,
        is_active BOOLEAN NOT NULL,
        created_at TIMESTAMPTZ NOT NULL,
        updated_at TIMESTAMPTZ NOT NULL,
        CONSTRAINT pk_customers PRIMARY KEY (id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS visits (
        id VARCHAR NOT NULL,
        customer_id VARCHAR NOT NULL,
        source VARCHAR(50) NOT NULL,
        recognition_event_id VARCHAR,
        visited_at TIMESTAMPTZ NOT NULL,
        order_note TEXT,
        outlet_id VARCHAR NOT NULL,
        CONSTRAINT pk_visits PRIMARY KEY (id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS partners (
        id VARCHAR NOT NULL,
        name VARCHAR(120) NOT NULL,
        type VARCHAR(20) NOT NULL,
        address VARCHAR(255),
        pic_name VARCHAR(100),
        pic_phone VARCHAR(20),
        pic_email VARCHAR(254),
        tax_id VARCHAR(30),
        contract_start DATE NOT NULL,
        contract_end DATE NOT NULL,
        invite_code VARCHAR(12) NOT NULL,
        is_active BOOLEAN NOT NULL,
        notes TEXT,
        created_at TIMESTAMPTZ NOT NULL,
        updated_at TIMESTAMPTZ NOT NULL,
        CONSTRAINT pk_partners PRIMARY KEY (id),
        CONSTRAINT unique_partners_invite_code UNIQUE (invite_code),
        CONSTRAINT check_partners_contract_order CHECK (contract_end >= contract_start),
        CONSTRAINT check_partners_type_enum CHECK (type IN ('foundation', 'company', 'school', 'community', 'other'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS partner_employees (
        id VARCHAR NOT NULL,
        partner_id VARCHAR NOT NULL,
        name VARCHAR(100) NOT NULL,
        phone VARCHAR(20),
        employee_number VARCHAR(50),
        discount_percent INTEGER,
        flat_discount NUMERIC(12, 2),
        monthly_open_table NUMERIC(12, 2),
        monthly_quota NUMERIC(12, 2),
        valid_until DATE,
        status VARCHAR(10) NOT NULL,
        customer_id VARCHAR,
        joined_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ NOT NULL,
        updated_at TIMESTAMPTZ NOT NULL,
        CONSTRAINT pk_partner_employees PRIMARY KEY (id),
        CONSTRAINT check_partner_employees_discount_percent_range CHECK (discount_percent >= 1 AND discount_percent <= 100),
        CONSTRAINT check_partner_employees_flat_discount_whole CHECK (flat_discount > 0 AND flat_discount = trunc(flat_discount)),
        CONSTRAINT check_partner_employees_monthly_open_table_whole CHECK (monthly_open_table > 0 AND monthly_open_table = trunc(monthly_open_table)),
        CONSTRAINT check_partner_employees_monthly_quota_whole CHECK (monthly_quota > 0 AND monthly_quota = trunc(monthly_quota)),
        CONSTRAINT check_partner_employees_status_enum CHECK (status IN ('pending', 'active', 'review', 'inactive', 'rejected'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS partner_employee_free_menus (
        id VARCHAR NOT NULL,
        employee_id VARCHAR NOT NULL,
        menu_item_id VARCHAR NOT NULL,
        daily_limit INTEGER NOT NULL,
        CONSTRAINT pk_partner_employee_free_menus PRIMARY KEY (id),
        CONSTRAINT unique_partner_employee_free_menus_employee_id_menu_item_id UNIQUE (employee_id, menu_item_id),
        CONSTRAINT check_partner_employee_free_menus_daily_limit_min CHECK (daily_limit >= 1)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS benefit_usages (
        id VARCHAR NOT NULL,
        partner_id VARCHAR NOT NULL,
        employee_id VARCHAR NOT NULL,
        order_id VARCHAR NOT NULL,
        kind VARCHAR(10) NOT NULL,
        amount NUMERIC(12, 2) NOT NULL,
        used_on DATE NOT NULL,
        created_at TIMESTAMPTZ NOT NULL,
        menu_item_id VARCHAR,
        qty INTEGER,
        CONSTRAINT pk_benefit_usages PRIMARY KEY (id),
        CONSTRAINT check_benefit_usages_amount_positive CHECK (amount > 0),
        CONSTRAINT check_benefit_usages_kind_enum CHECK (kind IN ('discount', 'flat', 'free', 'open_table'))
    )
    """,
)

ORDER_COLUMNS = (
    'ALTER TABLE orders ADD COLUMN IF NOT EXISTS customer_id VARCHAR',
    'ALTER TABLE orders ADD COLUMN IF NOT EXISTS partner_covered NUMERIC(12, 2) NOT NULL DEFAULT 0',
)

# Setiap kunci asing punya indeks dengan kolomnya di depan; kunci utama dan indeks unik yang sudah di depan tidak diulang.
INDEXES = (
    'CREATE INDEX IF NOT EXISTS index_customers_on_contact_digits ON customers (regexp_replace(contact, \'[^0-9]\', \'\', \'g\'))',
    'CREATE INDEX IF NOT EXISTS index_customers_on_name ON customers USING gin (name {trigram})',
    'CREATE INDEX IF NOT EXISTS index_visits_on_customer_id_and_visited_at ON visits (customer_id, visited_at)',
    'CREATE INDEX IF NOT EXISTS index_visits_on_outlet_id_and_visited_at ON visits (outlet_id, visited_at)',
    'CREATE INDEX IF NOT EXISTS index_visits_on_visited_at ON visits (visited_at)',
    'CREATE INDEX IF NOT EXISTS index_partners_on_name_and_id ON partners (name, id)',
    'CREATE INDEX IF NOT EXISTS index_partners_on_is_active_and_name_and_id ON partners (is_active DESC, name, id)',
    'CREATE INDEX IF NOT EXISTS index_partner_employees_on_partner_id_and_name_and_id ON partner_employees (partner_id, name, id)',
    'CREATE INDEX IF NOT EXISTS index_partner_employees_on_partner_id_and_status ON partner_employees (partner_id, status)',
    'CREATE INDEX IF NOT EXISTS index_partner_employees_on_customer_id ON partner_employees (customer_id)',
    "CREATE UNIQUE INDEX IF NOT EXISTS unique_partner_employees_customer_id_active ON partner_employees (customer_id) WHERE status IN ('active', 'review')",
    "CREATE UNIQUE INDEX IF NOT EXISTS unique_partner_employees_partner_id_phone ON partner_employees (partner_id, phone) WHERE phone IS NOT NULL AND status NOT IN ('review', 'rejected')",
    'CREATE INDEX IF NOT EXISTS index_partner_employee_free_menus_on_menu_item_id ON partner_employee_free_menus (menu_item_id)',
    'CREATE INDEX IF NOT EXISTS index_benefit_usages_on_employee_id_and_used_on ON benefit_usages (employee_id, used_on) INCLUDE (kind, amount, menu_item_id, qty)',
    'CREATE INDEX IF NOT EXISTS index_benefit_usages_on_order_id ON benefit_usages (order_id)',
    'CREATE INDEX IF NOT EXISTS index_benefit_usages_on_partner_id_and_used_on ON benefit_usages (partner_id, used_on) INCLUDE (amount, order_id)',
    'CREATE INDEX IF NOT EXISTS index_benefit_usages_on_used_on_and_partner_id ON benefit_usages (used_on, partner_id) INCLUDE (amount, order_id)',
    'CREATE INDEX IF NOT EXISTS index_benefit_usages_on_menu_item_id ON benefit_usages (menu_item_id)',
    'CREATE INDEX IF NOT EXISTS index_orders_on_customer_id ON orders (customer_id)',
    'CREATE INDEX IF NOT EXISTS index_orders_on_customer_id_and_created_at_and_id ON orders (customer_id, created_at DESC, id DESC) WHERE customer_id IS NOT NULL AND voided_at IS NULL',
)

# (tabel, nama, kolom, tujuan, aksi). Semua aksi ke pelanggan, mitra, dan pesanan adalah RESTRICT, berbeda dari FOMO: riwayat kunjungan, pesanan, dan tagihan mitra
# tidak boleh hilang atau terlepas diam-diam (aturan 4.4.3), dan pelanggan, mitra, serta karyawan mitra dinonaktifkan lewat status, bukan dihapus (aturan 4.4.4).
# Kode yang menghapus pesanan menghapus pemakaian benefitnya secara eksplisit. Pelanggan sengaja lintas cabang (tanpa kolom cabang): satu orang bisa datang ke
# beberapa cabang; cabang yang dihapus menghapus kunjungannya lewat visits.outlet_id, dan pelanggannya tetap ada.
FOREIGN_KEYS = (
    ('visits', 'fk_visits_customer_id_customers', 'customer_id', 'customers', 'RESTRICT'),
    ('visits', 'fk_visits_outlet_id_outlets', 'outlet_id', 'outlets', 'RESTRICT'),
    ('partner_employees', 'fk_partner_employees_partner_id_partners', 'partner_id', 'partners', 'RESTRICT'),
    ('partner_employees', 'fk_partner_employees_customer_id_customers', 'customer_id', 'customers', 'RESTRICT'),
    ('partner_employee_free_menus', 'fk_partner_employee_free_menus_employee_id_partner_employees', 'employee_id', 'partner_employees', 'RESTRICT'),
    ('partner_employee_free_menus', 'fk_partner_employee_free_menus_menu_item_id_menu_items', 'menu_item_id', 'menu_items', 'RESTRICT'),
    ('benefit_usages', 'fk_benefit_usages_partner_id_partners', 'partner_id', 'partners', 'RESTRICT'),
    ('benefit_usages', 'fk_benefit_usages_employee_id_partner_employees', 'employee_id', 'partner_employees', 'RESTRICT'),
    ('benefit_usages', 'fk_benefit_usages_order_id_orders', 'order_id', 'orders', 'RESTRICT'),
    ('benefit_usages', 'fk_benefit_usages_menu_item_id_menu_items', 'menu_item_id', 'menu_items', 'SET NULL'),
    ('orders', 'fk_orders_customer_id_customers', 'customer_id', 'customers', 'RESTRICT'),
)


def _foreign_key(table: str, name: str, column: str, target: str, action: str) -> str:
    return f"""
    DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE connamespace = current_schema()::regnamespace AND conname = '{name}') THEN
            ALTER TABLE {table} ADD CONSTRAINT {name} FOREIGN KEY ({column}) REFERENCES {target}(id) ON DELETE {action} NOT VALID;
        END IF;
    END $$;
    """


ACTION_CODES = {'CASCADE': 'c', 'RESTRICT': 'r', 'SET NULL': 'n'}
# Kolom yang sempat dibuat bertipe UUID; semua id proyek ini teks (aturan 4.2.6).
UUID_COLUMNS = (
    ('partners', 'id'),
    ('partner_employees', 'id'),
    ('partner_employees', 'partner_id'),
    ('partner_employee_free_menus', 'id'),
    ('partner_employee_free_menus', 'employee_id'),
    ('benefit_usages', 'id'),
    ('benefit_usages', 'partner_id'),
    ('benefit_usages', 'employee_id'),
)
PARTNER_TABLES = frozenset(table for table, _column in UUID_COLUMNS)


def _repair_earlier_run() -> None:
    """Database yang sudah menjalankan versi lama berkas ini: kunci asing yang salah aksi atau terikat kolom UUID dibuang lalu dibuat ulang di bawah, dan kolom UUID dijadikan teks."""
    bind = op.get_bind()
    uuid_columns = [
        (table, column)
        for table, column in UUID_COLUMNS
        if bind.execute(
            text('SELECT data_type FROM information_schema.columns WHERE table_schema = current_schema() AND table_name = :t AND column_name = :c'),
            {'t': table, 'c': column},
        ).scalar() == 'uuid'
    ]
    for table, name, _column, target, action in FOREIGN_KEYS:
        current = bind.execute(text('SELECT confdeltype FROM pg_constraint WHERE connamespace = current_schema()::regnamespace AND conname = :name'), {'name': name}).scalar()
        if current is None:
            continue
        if current != ACTION_CODES[action] or (uuid_columns and (table in PARTNER_TABLES or target in PARTNER_TABLES)):
            op.execute(f'ALTER TABLE {table} DROP CONSTRAINT {name}')
    for table, column in uuid_columns:
        op.execute(f'ALTER TABLE {table} ALTER COLUMN {column} TYPE VARCHAR USING {column}::text')


def upgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    for statement in TABLES:
        op.execute(statement)
    _repair_earlier_run()
    for statement in ORDER_COLUMNS:
        op.execute(statement)
    trigram = trigram_opclass(op.get_bind())
    for statement in (index.replace('{trigram}', trigram) for index in INDEXES):
        op.execute(statement)
    for table, name, column, target, action in FOREIGN_KEYS:
        op.execute(_foreign_key(table, name, column, target, action))
    for table, name, _column, _target, _action in FOREIGN_KEYS:
        op.execute(f'ALTER TABLE {table} VALIDATE CONSTRAINT {name}')


def downgrade() -> None:
    # Tidak ada aksi: membuang tabel ini menghapus data pelanggan dan benefit mitra; kesalahan setelah rilis diperbaiki dengan migrasi maju.
    pass
