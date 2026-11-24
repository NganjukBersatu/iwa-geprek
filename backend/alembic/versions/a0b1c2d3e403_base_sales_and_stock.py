"""base schema: shift codes, cash sessions, orders, expenses, overpayments, stock and ingredient cards

Revision ID: a0b1c2d3e403
Revises: a0b1c2d3e402

The v2 chain started on top of tables owned by a legacy chain that is not in this repository, so a database built from nothing
could not be created. This revision and its three siblings create those tables, in the shape the chain expects to find them:
columns that later revisions add (roles.is_admin, expenses.bahan_id, the business_day columns, ...) are left out on purpose.

Every statement is IF NOT EXISTS, so a database that already has the tables (production, staging) is left exactly as it is.
Down is a no-op: dropping the core tables would destroy data, and a mistake after release is fixed with a forward migration.
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'a0b1c2d3e403'
down_revision: Union[str, Sequence[str], None] = 'a0b1c2d3e402'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS kode_shift (
        id VARCHAR NOT NULL,
        outlet_id VARCHAR NOT NULL,
        master_id VARCHAR,
        kode VARCHAR(20) NOT NULL,
        jam_mulai VARCHAR(5),
        jam_selesai VARCHAR(5),
        warna VARCHAR(9),
        duration_minutes INTEGER,
        lembur_mulai VARCHAR(5),
        lembur_selesai VARCHAR(5),
        kategori_id VARCHAR,
        libur BOOLEAN DEFAULT false NOT NULL,
        urutan INTEGER NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE,
        updated_at TIMESTAMP WITH TIME ZONE,
        CONSTRAINT pk_kode_shift PRIMARY KEY (id),
        CONSTRAINT fk_kode_shift_outlet_id_outlets FOREIGN KEY(outlet_id) REFERENCES outlets (id) ON DELETE CASCADE,
        CONSTRAINT fk_kode_shift_kategori_id_kategori FOREIGN KEY(kategori_id) REFERENCES kategori (id) ON DELETE SET NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_kode_shift_on_outlet_id ON kode_shift (outlet_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_kode_shift_on_kategori_id ON kode_shift (kategori_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS shifts (
        id VARCHAR NOT NULL,
        outlet_id VARCHAR NOT NULL,
        kasir_id VARCHAR NOT NULL,
        kode_shift_id VARCHAR,
        kode_shift VARCHAR(20),
        kode_shift_warna VARCHAR(9),
        start_time TIMESTAMP WITH TIME ZONE NOT NULL,
        end_time TIMESTAMP WITH TIME ZONE,
        modal_awal NUMERIC(12, 2) NOT NULL,
        total_pendapatan_sistem NUMERIC(12, 2) NOT NULL,
        total_pendapatan_tunai NUMERIC(12, 2) NOT NULL,
        total_pengeluaran_kas_laci NUMERIC(12, 2) NOT NULL,
        uang_aktual NUMERIC(12, 2),
        selisih NUMERIC(12, 2),
        plot_modal NUMERIC(12, 2),
        plot_belanja NUMERIC(12, 2),
        aktual_modal NUMERIC(12, 2),
        aktual_belanja NUMERIC(12, 2),
        aktual_omzet NUMERIC(12, 2),
        catatan VARCHAR(500),
        status shift_status NOT NULL,
        CONSTRAINT pk_shifts PRIMARY KEY (id),
        CONSTRAINT fk_shifts_outlet_id_outlets FOREIGN KEY(outlet_id) REFERENCES outlets (id) ON DELETE RESTRICT,
        CONSTRAINT fk_shifts_kasir_id_staff FOREIGN KEY(kasir_id) REFERENCES staff (id) ON DELETE RESTRICT,
        CONSTRAINT fk_shifts_kode_shift_id_kode_shift FOREIGN KEY(kode_shift_id) REFERENCES kode_shift (id) ON DELETE SET NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_shifts_on_kasir_id ON shifts (kasir_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_shifts_on_kode_shift_id ON shifts (kode_shift_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS orders (
        id VARCHAR NOT NULL,
        shift_id VARCHAR NOT NULL,
        outlet_id VARCHAR NOT NULL,
        kasir_id VARCHAR NOT NULL,
        customer_name VARCHAR(255),
        table_no VARCHAR(32),
        order_type VARCHAR(16) NOT NULL,
        kategori_pengunjung_id VARCHAR,
        kategori_pengunjung_label VARCHAR(40),
        gender_pengunjung_id VARCHAR,
        gender_pengunjung_label VARCHAR(40),
        catatan_id VARCHAR,
        catatan_label VARCHAR(100),
        nomor_nota VARCHAR(40),
        client_id VARCHAR(64),
        payment_method VARCHAR(16),
        payment_method_label VARCHAR(40),
        metode_bayar_id VARCHAR,
        cash_received NUMERIC(12, 2),
        promo_diskon_id VARCHAR,
        diskon NUMERIC(12, 2) NOT NULL,
        total NUMERIC(12, 2) NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        voided_at TIMESTAMP WITH TIME ZONE,
        void_reason VARCHAR(255),
        voided_by VARCHAR,
        status_pesanan VARCHAR(16) NOT NULL,
        selesai_at TIMESTAMP WITH TIME ZONE,
        CONSTRAINT pk_orders PRIMARY KEY (id),
        CONSTRAINT fk_orders_shift_id_shifts FOREIGN KEY(shift_id) REFERENCES shifts (id) ON DELETE RESTRICT,
        CONSTRAINT fk_orders_outlet_id_outlets FOREIGN KEY(outlet_id) REFERENCES outlets (id) ON DELETE RESTRICT,
        CONSTRAINT fk_orders_kasir_id_staff FOREIGN KEY(kasir_id) REFERENCES staff (id) ON DELETE RESTRICT,
        CONSTRAINT fk_orders_kategori_pengunjung_id_kategori_pengunjung FOREIGN KEY(kategori_pengunjung_id) REFERENCES kategori_pengunjung (id) ON DELETE SET NULL,
        CONSTRAINT fk_orders_gender_pengunjung_id_gender_pengunjung FOREIGN KEY(gender_pengunjung_id) REFERENCES gender_pengunjung (id) ON DELETE SET NULL,
        CONSTRAINT fk_orders_catatan_id_kategori FOREIGN KEY(catatan_id) REFERENCES kategori (id) ON DELETE SET NULL,
        CONSTRAINT fk_orders_metode_bayar_id_metode_bayar FOREIGN KEY(metode_bayar_id) REFERENCES metode_bayar (id) ON DELETE SET NULL,
        CONSTRAINT fk_orders_promo_diskon_id_promo_diskon FOREIGN KEY(promo_diskon_id) REFERENCES promo_diskon (id) ON DELETE SET NULL,
        CONSTRAINT fk_orders_voided_by_staff FOREIGN KEY(voided_by) REFERENCES staff (id) ON DELETE SET NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_orders_on_kasir_id ON orders (kasir_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_orders_on_kategori_pengunjung_id ON orders (kategori_pengunjung_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_orders_on_gender_pengunjung_id ON orders (gender_pengunjung_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_orders_on_metode_bayar_id ON orders (metode_bayar_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_orders_on_voided_by ON orders (voided_by)
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS unique_orders_client_id ON orders (client_id) WHERE client_id IS NOT NULL
    """,
    """
    CREATE TABLE IF NOT EXISTS order_items (
        id VARCHAR NOT NULL,
        order_id VARCHAR NOT NULL,
        menu_item_id VARCHAR,
        menu_item_name VARCHAR(255) NOT NULL,
        unit_price NUMERIC(10, 2) NOT NULL,
        hpp_satuan NUMERIC(12, 2),
        qty INTEGER NOT NULL,
        subtotal NUMERIC(12, 2) NOT NULL,
        note VARCHAR(255),
        CONSTRAINT pk_order_items PRIMARY KEY (id),
        CONSTRAINT fk_order_items_order_id_orders FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE CASCADE,
        CONSTRAINT fk_order_items_menu_item_id_menu_items FOREIGN KEY(menu_item_id) REFERENCES menu_items (id) ON DELETE SET NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_order_items_on_order_id ON order_items (order_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_order_items_on_menu_item_id ON order_items (menu_item_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS order_item_opsi (
        id VARCHAR NOT NULL,
        order_item_id VARCHAR NOT NULL,
        jenis VARCHAR(8) NOT NULL,
        ref_id VARCHAR,
        grup_nama VARCHAR(80),
        nama VARCHAR(80) NOT NULL,
        warna VARCHAR(9),
        harga NUMERIC(10, 2) NOT NULL,
        qty INTEGER NOT NULL,
        hpp_satuan NUMERIC(12, 2),
        CONSTRAINT pk_order_item_opsi PRIMARY KEY (id),
        CONSTRAINT fk_order_item_opsi_order_item_id_order_items FOREIGN KEY(order_item_id) REFERENCES order_items (id) ON DELETE CASCADE
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_order_item_opsi_on_order_item_id ON order_item_opsi (order_item_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS nota_counter (
        outlet_id VARCHAR NOT NULL,
        tanggal DATE NOT NULL,
        urutan INTEGER NOT NULL,
        CONSTRAINT pk_nota_counter PRIMARY KEY (outlet_id, tanggal),
        CONSTRAINT fk_nota_counter_outlet_id_outlets FOREIGN KEY(outlet_id) REFERENCES outlets (id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS kelebihan_bayar (
        id VARCHAR NOT NULL,
        order_id VARCHAR NOT NULL,
        outlet_id VARCHAR NOT NULL,
        shift_id VARCHAR,
        kasir_id VARCHAR,
        kasir_nama VARCHAR(255) NOT NULL,
        metode_kode VARCHAR(16) NOT NULL,
        metode_label VARCHAR(40) NOT NULL,
        total_pesanan NUMERIC(12, 2) NOT NULL,
        diterima NUMERIC(12, 2) NOT NULL,
        jumlah NUMERIC(12, 2) NOT NULL,
        waktu TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_kelebihan_bayar PRIMARY KEY (id),
        CONSTRAINT fk_kelebihan_bayar_order_id_orders FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE CASCADE,
        CONSTRAINT fk_kelebihan_bayar_outlet_id_outlets FOREIGN KEY(outlet_id) REFERENCES outlets (id) ON DELETE RESTRICT,
        CONSTRAINT fk_kelebihan_bayar_shift_id_shifts FOREIGN KEY(shift_id) REFERENCES shifts (id) ON DELETE SET NULL,
        CONSTRAINT fk_kelebihan_bayar_kasir_id_staff FOREIGN KEY(kasir_id) REFERENCES staff (id) ON DELETE SET NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_kelebihan_bayar_on_shift_id ON kelebihan_bayar (shift_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_kelebihan_bayar_on_kasir_id ON kelebihan_bayar (kasir_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS pengajuan_pembatalan_order (
        id VARCHAR NOT NULL,
        order_id VARCHAR NOT NULL,
        outlet_id VARCHAR NOT NULL,
        diajukan_oleh_id VARCHAR NOT NULL,
        alasan TEXT,
        status status_pengajuan_pembatalan NOT NULL,
        diputus_oleh_id VARCHAR,
        diputus_pada TIMESTAMP WITH TIME ZONE,
        catatan_atasan TEXT,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_pengajuan_pembatalan_order PRIMARY KEY (id),
        CONSTRAINT fk_pengajuan_pembatalan_order_order_id_orders FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE CASCADE,
        CONSTRAINT fk_pengajuan_pembatalan_order_outlet_id_outlets FOREIGN KEY(outlet_id) REFERENCES outlets (id) ON DELETE RESTRICT,
        CONSTRAINT fk_pengajuan_pembatalan_order_diajukan_oleh_id_staff FOREIGN KEY(diajukan_oleh_id) REFERENCES staff (id) ON DELETE RESTRICT,
        CONSTRAINT fk_pengajuan_pembatalan_order_diputus_oleh_id_staff FOREIGN KEY(diputus_oleh_id) REFERENCES staff (id) ON DELETE SET NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_pengajuan_pembatalan_order_on_order_id ON pengajuan_pembatalan_order (order_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_pengajuan_pembatalan_order_on_outlet_id ON pengajuan_pembatalan_order (outlet_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_pengajuan_pembatalan_order_on_diajukan_oleh_id ON pengajuan_pembatalan_order (diajukan_oleh_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_pengajuan_pembatalan_order_on_diputus_oleh_id ON pengajuan_pembatalan_order (diputus_oleh_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS expenses (
        id VARCHAR NOT NULL,
        outlet_id VARCHAR NOT NULL,
        shift_id VARCHAR,
        kasir_id VARCHAR NOT NULL,
        item_rutin_id VARCHAR,
        nama_item VARCHAR(255) NOT NULL,
        jumlah NUMERIC(12, 2) NOT NULL,
        sumber_dana sumber_dana NOT NULL,
        catatan TEXT,
        pembeli VARCHAR(120),
        bukti_path VARCHAR(500),
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_expenses PRIMARY KEY (id),
        CONSTRAINT fk_expenses_outlet_id_outlets FOREIGN KEY(outlet_id) REFERENCES outlets (id) ON DELETE RESTRICT,
        CONSTRAINT fk_expenses_shift_id_shifts FOREIGN KEY(shift_id) REFERENCES shifts (id) ON DELETE SET NULL,
        CONSTRAINT fk_expenses_kasir_id_staff FOREIGN KEY(kasir_id) REFERENCES staff (id) ON DELETE RESTRICT,
        CONSTRAINT fk_expenses_item_rutin_id_item_rutin FOREIGN KEY(item_rutin_id) REFERENCES item_rutin (id) ON DELETE SET NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_expenses_on_shift_id ON expenses (shift_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_expenses_on_kasir_id ON expenses (kasir_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_expenses_on_item_rutin_id ON expenses (item_rutin_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS stok_item (
        id VARCHAR NOT NULL,
        outlet_id VARCHAR NOT NULL,
        menu_item_id VARCHAR NOT NULL,
        satuan_id VARCHAR,
        minimum NUMERIC(12, 3) NOT NULL,
        dilacak BOOLEAN NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_stok_item PRIMARY KEY (id),
        CONSTRAINT fk_stok_item_outlet_id_outlets FOREIGN KEY(outlet_id) REFERENCES outlets (id) ON DELETE RESTRICT,
        CONSTRAINT fk_stok_item_menu_item_id_menu_items FOREIGN KEY(menu_item_id) REFERENCES menu_items (id) ON DELETE CASCADE,
        CONSTRAINT fk_stok_item_satuan_id_satuan FOREIGN KEY(satuan_id) REFERENCES satuan (id) ON DELETE SET NULL,
        CONSTRAINT unique_stok_item_outlet_id_and_menu_item_id UNIQUE (outlet_id, menu_item_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_stok_item_on_menu_item_id ON stok_item (menu_item_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_stok_item_on_satuan_id ON stok_item (satuan_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS kartu_stok (
        id VARCHAR NOT NULL,
        outlet_id VARCHAR NOT NULL,
        menu_item_id VARCHAR,
        menu_item_name VARCHAR(255) NOT NULL,
        jenis VARCHAR(20) NOT NULL,
        qty NUMERIC(12, 3) NOT NULL,
        harga_satuan NUMERIC(12, 2),
        hpp_setelah NUMERIC(12, 2),
        order_id VARCHAR,
        catatan VARCHAR(255),
        staff_id VARCHAR,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_kartu_stok PRIMARY KEY (id),
        CONSTRAINT fk_kartu_stok_outlet_id_outlets FOREIGN KEY(outlet_id) REFERENCES outlets (id) ON DELETE RESTRICT,
        CONSTRAINT fk_kartu_stok_menu_item_id_menu_items FOREIGN KEY(menu_item_id) REFERENCES menu_items (id) ON DELETE SET NULL,
        CONSTRAINT fk_kartu_stok_order_id_orders FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE SET NULL,
        CONSTRAINT fk_kartu_stok_staff_id_staff FOREIGN KEY(staff_id) REFERENCES staff (id) ON DELETE SET NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_kartu_stok_on_menu_item_id ON kartu_stok (menu_item_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_kartu_stok_on_order_id ON kartu_stok (order_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_kartu_stok_on_staff_id ON kartu_stok (staff_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS opname_bahan (
        id VARCHAR NOT NULL,
        outlet_id VARCHAR NOT NULL,
        dari DATE NOT NULL,
        sampai DATE NOT NULL,
        catatan VARCHAR(255),
        staff_id VARCHAR,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_opname_bahan PRIMARY KEY (id),
        CONSTRAINT fk_opname_bahan_outlet_id_outlets FOREIGN KEY(outlet_id) REFERENCES outlets (id) ON DELETE RESTRICT,
        CONSTRAINT fk_opname_bahan_staff_id_staff FOREIGN KEY(staff_id) REFERENCES staff (id) ON DELETE SET NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_opname_bahan_on_outlet_id ON opname_bahan (outlet_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_opname_bahan_on_staff_id ON opname_bahan (staff_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS opname_bahan_baris (
        id VARCHAR NOT NULL,
        opname_id VARCHAR NOT NULL,
        bahan_id VARCHAR,
        bahan_nama VARCHAR(255) NOT NULL,
        satuan_id VARCHAR,
        stok_akhir NUMERIC(12, 3) NOT NULL,
        real NUMERIC(12, 3) NOT NULL,
        nilai NUMERIC(14, 4) NOT NULL,
        toleransi_minus NUMERIC(5, 2) NOT NULL,
        CONSTRAINT pk_opname_bahan_baris PRIMARY KEY (id),
        CONSTRAINT fk_opname_bahan_baris_opname_id_opname_bahan FOREIGN KEY(opname_id) REFERENCES opname_bahan (id) ON DELETE CASCADE,
        CONSTRAINT fk_opname_bahan_baris_bahan_id_bahan FOREIGN KEY(bahan_id) REFERENCES bahan (id) ON DELETE SET NULL,
        CONSTRAINT fk_opname_bahan_baris_satuan_id_satuan FOREIGN KEY(satuan_id) REFERENCES satuan (id) ON DELETE SET NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_opname_bahan_baris_on_opname_id ON opname_bahan_baris (opname_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_opname_bahan_baris_on_bahan_id ON opname_bahan_baris (bahan_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_opname_bahan_baris_on_satuan_id ON opname_bahan_baris (satuan_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS kartu_bahan (
        id VARCHAR NOT NULL,
        outlet_id VARCHAR NOT NULL,
        bahan_id VARCHAR,
        bahan_nama VARCHAR(255) NOT NULL,
        jenis VARCHAR(20) NOT NULL,
        qty NUMERIC(12, 3) NOT NULL,
        harga_satuan NUMERIC(12, 2),
        expense_id VARCHAR,
        order_id VARCHAR,
        opname_id VARCHAR,
        sebab VARCHAR(30),
        bukti_path VARCHAR(255),
        catatan VARCHAR(255),
        staff_id VARCHAR,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_kartu_bahan PRIMARY KEY (id),
        CONSTRAINT fk_kartu_bahan_outlet_id_outlets FOREIGN KEY(outlet_id) REFERENCES outlets (id) ON DELETE RESTRICT,
        CONSTRAINT fk_kartu_bahan_bahan_id_bahan FOREIGN KEY(bahan_id) REFERENCES bahan (id) ON DELETE SET NULL,
        CONSTRAINT fk_kartu_bahan_expense_id_expenses FOREIGN KEY(expense_id) REFERENCES expenses (id) ON DELETE SET NULL,
        CONSTRAINT fk_kartu_bahan_order_id_orders FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE SET NULL,
        CONSTRAINT fk_kartu_bahan_opname_id_opname_bahan FOREIGN KEY(opname_id) REFERENCES opname_bahan (id) ON DELETE SET NULL,
        CONSTRAINT fk_kartu_bahan_staff_id_staff FOREIGN KEY(staff_id) REFERENCES staff (id) ON DELETE SET NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_kartu_bahan_on_expense_id ON kartu_bahan (expense_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_kartu_bahan_on_order_id ON kartu_bahan (order_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_kartu_bahan_on_opname_id ON kartu_bahan (opname_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_kartu_bahan_on_staff_id ON kartu_bahan (staff_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS validasi_nontunai (
        id VARCHAR NOT NULL,
        outlet_id VARCHAR NOT NULL,
        tanggal DATE NOT NULL,
        nominal_mbanking NUMERIC(14, 2) NOT NULL,
        diinput_oleh VARCHAR,
        diperbarui_pada TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_validasi_nontunai PRIMARY KEY (id),
        CONSTRAINT fk_validasi_nontunai_outlet_id_outlets FOREIGN KEY(outlet_id) REFERENCES outlets (id) ON DELETE RESTRICT,
        CONSTRAINT fk_validasi_nontunai_diinput_oleh_staff FOREIGN KEY(diinput_oleh) REFERENCES staff (id) ON DELETE SET NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_validasi_nontunai_on_outlet_id ON validasi_nontunai (outlet_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_validasi_nontunai_on_diinput_oleh ON validasi_nontunai (diinput_oleh)
    """,
)


def upgrade() -> None:
    for statement in STATEMENTS:
        op.execute(statement)


def downgrade() -> None:
    # Irreversible by design (see the module docstring): no table is dropped.
    pass
