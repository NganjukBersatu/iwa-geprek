"""english names: every table, column, enum type, and database function that still carried an Indonesian name gets an English one

Revision ID: j5o7g9i1c983
Revises: i3m5e7g9b871
Create Date: 2026-11-06 12:00:00.000000

Renaming is metadata only in PostgreSQL, so it takes no table rewrite and holds each lock for an instant. The new name of a column is the name its
model attribute already had, so the code and the database finally say the same thing. Constraint and index names are rebuilt from the new names
(pk_, fk_, index_<table>_on_<columns>, unique_, check_). The trigger functions are text, which a rename does not touch, so they are written again
with the new names; the check at the end refuses to finish if any function in the schema still mentions an old name.

Every step looks first and acts only when the old name is still there, so a second run changes nothing. A database built from nothing runs the whole
older chain with the old names and ends here with the new ones; an existing database ends in the same place.

Down does nothing: the old names are not worth restoring (the code no longer knows them), and a mistake after release is fixed with a forward migration.
"""
import logging
import re
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'j5o7g9i1c983'
down_revision: Union[str, Sequence[str], None] = 'i3m5e7g9b871'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

log = logging.getLogger('alembic.runtime.migration')
MAX_NAME_LENGTH = 63

TABLES = {
    'absensi': 'attendance_records',
    'bahan': 'ingredients',
    'ekstra': 'extras',
    'ekstra_harga_outlet': 'extra_outlet_prices',
    'ekstra_resep': 'extra_recipes',
    'gender_pengunjung': 'visitor_genders',
    'item_rutin': 'routine_items',
    'jadwal_libur': 'day_offs',
    'jadwal_shift': 'schedules',
    'kartu_bahan': 'ingredient_cards',
    'kartu_stok': 'stock_cards',
    'katalog_bahan': 'catalog_ingredients',
    'kategori': 'categories',
    'kategori_pengunjung': 'visitor_categories',
    'kelebihan_bayar': 'overpayments',
    'kode_shift': 'shift_codes',
    'lembur': 'overtime_records',
    'menu_ekstra': 'menu_extras',
    'menu_harga_outlet': 'menu_outlet_prices',
    'menu_varian_grup': 'menu_variant_groups',
    'metode_bayar': 'payment_methods',
    'nota_counter': 'receipt_counters',
    'opname_bahan': 'ingredient_counts',
    'opname_bahan_baris': 'ingredient_count_lines',
    'pengajuan_izin': 'leave_requests',
    'pengajuan_pembatalan_order': 'cancellation_requests',
    'pengaturan_kafe': 'cafe_settings',
    'perangkat': 'devices',
    'perangkat_tautan': 'device_links',
    'promo_diskon': 'promos',
    'promosi_cafe': 'cafe_promotions',
    'resep_add_cost': 'recipe_add_costs',
    'resep_bahan': 'recipe_ingredients',
    'satuan': 'units',
    'sop_draf': 'sop_drafts',
    'stok_item': 'stock_items',
    'tugas': 'tasks',
    'validasi_nontunai': 'non_cash_checks',
    'varian_grup': 'variant_groups',
    'varian_pilihan': 'variant_choices',
    'varian_pilihan_resep': 'variant_choice_recipes',
    'order_item_opsi': 'order_item_options',
}

ENUMS = {
    'status_pengajuan_pembatalan': 'cancellation_request_status',
    'sumber_dana': 'funding_source',
    'status_kehadiran': 'attendance_status',
    'jenis_pengajuan': 'leave_request_kind',
    'status_pengajuan': 'leave_request_status',
    'jenis_tugas': 'task_kind',
    'status_tugas': 'task_status',
}

# old table name -> {old column name: new column name}
COLUMNS = {
    'absensi': {
        'tanggal': 'date',
        'kode_shift_id': 'shift_code_id',
        'jadwal_id': 'schedule_id',
        'jam_masuk': 'clock_in_at',
        'jam_keluar': 'clock_out_at',
        'ditutup_otomatis': 'auto_closed',
        'tutup_otomatis_dilihat': 'notice_seen',
        'catatan': 'note',
        'alasan_di_luar_jadwal': 'outside_schedule_reason',
        'foto_path': 'clock_in_photo_path',
        'lat_masuk': 'clock_in_latitude',
        'lng_masuk': 'clock_in_longitude',
        'akurasi_masuk': 'clock_in_accuracy',
        'mode_masuk': 'clock_in_location_mode',
        'catatan_lokasi_masuk': 'clock_in_location_note',
        'jarak_masuk': 'clock_in_distance_meters',
        'radius_masuk': 'clock_in_radius_meters',
        'foto_pulang_path': 'clock_out_photo_path',
        'lat_pulang': 'clock_out_latitude',
        'lng_pulang': 'clock_out_longitude',
        'akurasi_pulang': 'clock_out_accuracy',
        'mode_pulang': 'clock_out_location_mode',
        'catatan_lokasi_pulang': 'clock_out_location_note',
        'jarak_pulang': 'clock_out_distance_meters',
        'radius_pulang': 'clock_out_radius_meters',
    },
    'promosi_cafe': {
        'judul': 'title',
        'deskripsi': 'description',
        'gambar_url': 'image',
        'tanggal_mulai': 'starts_on',
        'tanggal_selesai': 'ends_on',
        'aktif': 'is_active',
    },
    'pengaturan_kafe': {
        'id': 'outlet_id',
        'nama': 'name',
        'alamat': 'address',
        'telepon': 'phone',
        'nomor_aduan': 'complaint_number',
        'sosial': 'social',
        'ucapan_struk': 'receipt_greeting',
        'tahapan_pesanan': 'order_stages',
        'toleransi_telat_menit': 'late_tolerance_minutes',
        'potongan_telat_per_menit': 'late_penalty_per_minute',
        'batas_tutup_otomatis_jam': 'auto_close_after_hours',
        'markup_hpp_persen': 'cost_markup_percent',
        'target_margin_persen': 'target_margin_percent',
        'tax_persen': 'tax_percent',
        'service_persen': 'service_percent',
    },
    'pengajuan_pembatalan_order': {
        'diajukan_oleh_id': 'requested_by_id',
        'alasan': 'reason',
        'diputus_oleh_id': 'decided_by_id',
        'diputus_pada': 'decided_at',
        'catatan_atasan': 'manager_note',
    },
    'shifts': {
        'kasir_id': 'cashier_id',
        'kode_shift_id': 'shift_code_id',
        'kode_shift': 'shift_code',
        'kode_shift_warna': 'shift_code_color',
        'start_time': 'opened_at',
        'end_time': 'closed_at',
        'modal_awal': 'opening_cash',
        'total_pendapatan_sistem': 'system_revenue',
        'total_pendapatan_tunai': 'cash_revenue',
        'total_pengeluaran_kas_laci': 'drawer_expenses',
        'uang_aktual': 'actual_cash',
        'selisih': 'difference',
        'plot_modal': 'planned_float',
        'plot_belanja': 'planned_shopping',
        'aktual_modal': 'actual_float',
        'aktual_belanja': 'actual_shopping',
        'aktual_omzet': 'actual_revenue',
        'catatan': 'note',
    },
    'kategori': {
        'jenis': 'kind',
        'nama': 'name',
        'stasiun': 'station',
        'stasiun_id': 'station_id',
    },
    'satuan': {
        'nama': 'name',
    },
    'jadwal_libur': {
        'tanggal': 'date',
        'kode_shift_id': 'shift_code_id',
        'catatan': 'note',
    },
    'perangkat': {
        'nama': 'name',
        'bagian': 'section',
        'kode_hash': 'code_hash',
        'kode_kedaluwarsa': 'code_expires_at',
        'merek': 'brand',
        'didaftarkan_oleh': 'registered_by',
        'dibuat_pada': 'created_at',
        'dipasangkan_pada': 'paired_at',
        'terakhir_dipakai': 'last_used_at',
    },
    'perangkat_tautan': {
        'perangkat_id': 'device_id',
        'kedaluwarsa': 'expires_at',
        'ditautkan_pada': 'linked_at',
        'dibuat_pada': 'created_at',
    },
    'expenses': {
        'shift_id': 'cash_session_id',
        'kasir_id': 'cashier_id',
        'item_rutin_id': 'routine_item_id',
        'nama_item': 'item_name',
        'jumlah': 'amount',
        'sumber_dana': 'fund_source',
        'catatan': 'note',
        'pembeli': 'buyer',
        'bukti_path': 'receipt_path',
        'bahan_id': 'ingredient_id',
        'qty': 'quantity',
        'satuan_id': 'unit_id',
    },
    'ekstra': {
        'nama': 'name',
        'harga': 'price',
        'aktif': 'is_active',
        'kategori_id': 'category_id',
        'urutan': 'position',
    },
    'ekstra_harga_outlet': {
        'ekstra_id': 'extra_id',
        'harga': 'price',
    },
    'menu_ekstra': {
        'ekstra_id': 'extra_id',
    },
    'ekstra_resep': {
        'ekstra_id': 'extra_id',
        'bahan_id': 'ingredient_id',
        'katalog_id': 'catalog_id',
    },
    'katalog_bahan': {
        'nama': 'name',
        'satuan_id': 'unit_id',
    },
    'bahan': {
        'katalog_id': 'catalog_id',
        'nama': 'name',
        'kategori_id': 'category_id',
        'satuan_id': 'unit_id',
        'foto_path': 'photo_path',
        'harga_kemasan': 'package_price',
        'isi_kemasan': 'package_size',
        'harga_satuan': 'unit_price',
        'toleransi_minus': 'shrink_tolerance',
        'aktif': 'is_active',
        'tersedia': 'is_available',
        'saldo': 'balance',
    },
    'kartu_bahan': {
        'bahan_id': 'ingredient_id',
        'bahan_nama': 'ingredient_name',
        'jenis': 'kind',
        'harga_satuan': 'unit_price',
        'opname_id': 'count_id',
        'sebab': 'cause',
        'bukti_path': 'proof_path',
        'catatan': 'note',
    },
    'opname_bahan': {
        'dari': 'period_start',
        'sampai': 'period_end',
        'catatan': 'note',
    },
    'opname_bahan_baris': {
        'opname_id': 'count_id',
        'bahan_id': 'ingredient_id',
        'bahan_nama': 'ingredient_name',
        'satuan_id': 'unit_id',
        'stok_akhir': 'book_balance',
        'real': 'counted',
        'nilai': 'value',
        'toleransi_minus': 'shrink_tolerance',
    },
    'resep_bahan': {
        'bahan_id': 'ingredient_id',
        'katalog_id': 'catalog_id',
    },
    'pengajuan_izin': {
        'jenis': 'type',
        'tanggal_mulai': 'start_date',
        'tanggal_selesai': 'end_date',
        'alasan': 'reason',
        'diputus_oleh_id': 'decided_by_id',
        'diputus_pada': 'decided_at',
        'catatan_atasan': 'manager_note',
        'lampiran_path': 'attachment_path',
        'lampiran_link': 'attachment_link',
    },
    'menu_items': {
        'kategori_id': 'category_id',
        'punya_varian_suhu': 'has_temperature_variant',
        'tax_persen': 'tax_percent',
        'service_persen': 'service_percent',
    },
    'orders': {
        'shift_id': 'cash_session_id',
        'kasir_id': 'cashier_id',
        'kategori_pengunjung_id': 'visitor_category_id',
        'kategori_pengunjung_label': 'visitor_category_label',
        'gender_pengunjung_id': 'visitor_gender_id',
        'gender_pengunjung_label': 'visitor_gender_label',
        'catatan_id': 'note_id',
        'catatan_label': 'note_label',
        'nomor_nota': 'receipt_number',
        'metode_bayar_id': 'payment_method_id',
        'promo_diskon_id': 'promo_id',
        'diskon': 'discount',
        'voided_by': 'voided_by_id',
        'status_pesanan': 'serving_status',
        'selesai_at': 'served_at',
    },
    'order_items': {
        'hpp_satuan': 'unit_cost',
    },
    'order_item_opsi': {
        'jenis': 'kind',
        'grup_nama': 'group_name',
        'nama': 'name',
        'warna': 'color',
        'harga': 'price',
        'hpp_satuan': 'unit_cost',
    },
    'outlets': {
        'nama': 'name',
        'kode': 'code',
        'nomor': 'receipt_number',
        'aktif': 'is_active',
        'lat': 'latitude',
        'lng': 'longitude',
        'radius_absen_m': 'attendance_radius_meters',
        'plot_modal_laci': 'cash_float',
        'plot_uang_belanja': 'spending_float',
    },
    'outlet_tasks': {
        'created_by_id': 'creator_id',
        'completed_by_id': 'completer_id',
    },
    'kelebihan_bayar': {
        'shift_id': 'cash_session_id',
        'kasir_id': 'cashier_id',
        'kasir_nama': 'cashier_name',
        'metode_kode': 'method_code',
        'metode_label': 'method_label',
        'total_pesanan': 'order_total',
        'diterima': 'received',
        'jumlah': 'amount',
        'waktu': 'recorded_at',
    },
    'lembur': {
        'tanggal': 'date',
        'mulai': 'start_at',
        'selesai': 'end_at',
        'catatan': 'note',
    },
    'metode_bayar': {
        'kode': 'code',
        'ikon': 'icon',
        'urutan': 'position',
        'aktif': 'is_active',
        'butuh_kembalian': 'needs_change',
        'gambar_path': 'image_path',
        'catatan': 'note',
        'biaya_persen': 'fee_percent',
    },
    'promo_diskon': {
        'nama': 'name',
        'deskripsi': 'description',
        'jenis': 'kind',
        'tipe_diskon': 'discount_type',
        'nilai': 'value',
        'produk_berlaku': 'applies_to',
        'produk_ids': 'product_ids',
        'min_belanja': 'minimum_spend',
        'metode_aktivasi': 'activation',
        'tanggal_mulai': 'starts_on',
        'tanggal_selesai': 'ends_on',
        'aktif': 'is_active',
    },
    'nota_counter': {
        'tanggal': 'day',
        'urutan': 'sequence',
    },
    'resep_add_cost': {
        'jenis': 'kind',
        'nilai': 'value',
        'target_margin_persen': 'target_margin_percent',
    },
    'roles': {
        'nama': 'name',
        'keterangan': 'description',
        'izin': 'permissions',
        'bawaan': 'is_default',
        'urutan': 'sort_order',
    },
    'item_rutin': {
        'nama_item': 'name',
        'siklus_hari': 'cycle_days',
    },
    'jadwal_shift': {
        'tanggal': 'date',
        'kasir_id': 'staff_id',
        'kode_shift_id': 'shift_code_id',
        'catatan': 'note',
    },
    'kode_shift': {
        'kode': 'code',
        'jam_mulai': 'start_clock',
        'jam_selesai': 'end_clock',
        'warna': 'color',
        'lembur_mulai': 'overtime_start_clock',
        'lembur_selesai': 'overtime_end_clock',
        'kategori_id': 'category_id',
        'libur': 'is_day_off',
        'urutan': 'sort_order',
    },
    'sop_slide': {
        'urutan': 'sort_order',
        'judul': 'title',
        'isi': 'body',
    },
    'sop': {
        'judul': 'title',
        'aktif': 'active',
        'urutan': 'sort_order',
        'versi': 'version',
        'dibuat_oleh': 'created_by_id',
        'diubah_oleh': 'updated_by_id',
    },
    'sop_draf': {
        'versi_dasar': 'base_version',
        'isi': 'content',
        'diperbarui_pada': 'updated_at',
    },
    'staff': {
        'no_hp': 'phone',
        'alamat': 'address',
        'tanggal_lahir': 'birth_date',
        'jenis_kelamin': 'gender',
        'kontak_darurat_nama': 'emergency_name',
        'kontak_darurat_hp': 'emergency_phone',
        'kontak_darurat_hubungan': 'emergency_relation',
        'tanggal_bergabung': 'joined_date',
        'foto_key': 'photo_key',
        'dihapus_pada': 'deleted_at',
    },
    'stok_item': {
        'satuan_id': 'unit_id',
        'dilacak': 'is_tracked',
        'saldo': 'balance',
    },
    'kartu_stok': {
        'jenis': 'kind',
        'harga_satuan': 'unit_price',
        'hpp_setelah': 'cost_after',
        'catatan': 'note',
    },
    'stored_files': {
        'data': 'content',
    },
    'tugas': {
        'jenis': 'type',
        'judul': 'title',
        'keterangan': 'description',
        'ditugaskan_ke_id': 'assignee_id',
        'dibuat_oleh_id': 'creator_id',
        'foto_tugas_path': 'assignment_photo_path',
        'tenggat': 'due_at',
        'catatan_selesai': 'completion_note',
        'foto_selesai_path': 'completion_photo_path',
        'selesai_pada': 'completed_at',
    },
    'varian_grup': {
        'nama': 'name',
        'wajib': 'required',
        'urutan': 'position',
        'aktif': 'is_active',
    },
    'varian_pilihan': {
        'grup_id': 'group_id',
        'nama': 'name',
        'warna': 'color',
        'urutan': 'position',
        'aktif': 'is_active',
    },
    'menu_varian_grup': {
        'grup_id': 'group_id',
    },
    'varian_pilihan_resep': {
        'pilihan_id': 'choice_id',
        'bahan_id': 'ingredient_id',
        'katalog_id': 'catalog_id',
    },
    'kategori_pengunjung': {
        'nama': 'name',
        'tanya_gender': 'asks_gender',
        'urutan': 'position',
        'aktif': 'is_active',
    },
    'gender_pengunjung': {
        'nama': 'name',
        'urutan': 'position',
        'aktif': 'is_active',
    },
    'validasi_nontunai': {
        'tanggal': 'date',
        'nominal_mbanking': 'bank_amount',
        'diinput_oleh': 'entered_by',
        'diperbarui_pada': 'updated_at',
    },
}

# Triggers and functions that carried an old name, dropped before the tables move so nothing runs half renamed.
OLD_TRIGGERS = (
    ('kartu_bahan_saldo', 'kartu_bahan'),
    ('kartu_bahan_business_day', 'kartu_bahan'),
    ('kartu_stok_saldo', 'kartu_stok'),
    ('kartu_stok_business_day', 'kartu_stok'),
    ('stok_item_saldo_awal', 'stok_item'),
    ('kelebihan_bayar_business_day', 'kelebihan_bayar'),
    ('kelebihan_bayar_money_mark', 'kelebihan_bayar'),
    ('kelebihan_bayar_money_late', 'kelebihan_bayar'),
    ('kelebihan_bayar_money_change', 'kelebihan_bayar'),
)
OLD_FUNCTIONS = (
    'kartu_bahan_saldo()',
    'kartu_stok_saldo()',
    'stok_item_saldo_awal()',
    'kartu_stok_business_day()',
    'kartu_bahan_business_day()',
    'kelebihan_bayar_business_day()',
    'kelebihan_bayar_money_late()',
    'kelebihan_bayar_money_change()',
)

# ---- the functions, with the new names -------------------------------------------------------------------------------------------------------

FUNCTIONS = (
    """
CREATE OR REPLACE FUNCTION ingredient_card_balance() RETURNS trigger AS $$
BEGIN
    IF TG_OP IN ('UPDATE', 'DELETE') AND OLD.ingredient_id IS NOT NULL THEN
        UPDATE ingredients SET balance = balance - OLD.qty WHERE id = OLD.ingredient_id;
    END IF;
    IF TG_OP IN ('INSERT', 'UPDATE') AND NEW.ingredient_id IS NOT NULL THEN
        UPDATE ingredients SET balance = balance + NEW.qty WHERE id = NEW.ingredient_id;
    END IF;
    RETURN NULL;
END $$ LANGUAGE plpgsql;
""",
    """
CREATE OR REPLACE FUNCTION stock_card_balance() RETURNS trigger AS $$
BEGIN
    IF TG_OP IN ('UPDATE', 'DELETE') AND OLD.menu_item_id IS NOT NULL THEN
        UPDATE stock_items SET balance = balance - OLD.qty WHERE outlet_id = OLD.outlet_id AND menu_item_id = OLD.menu_item_id;
    END IF;
    IF TG_OP IN ('INSERT', 'UPDATE') AND NEW.menu_item_id IS NOT NULL THEN
        UPDATE stock_items SET balance = balance + NEW.qty WHERE outlet_id = NEW.outlet_id AND menu_item_id = NEW.menu_item_id;
    END IF;
    RETURN NULL;
END $$ LANGUAGE plpgsql;
""",
    """
CREATE OR REPLACE FUNCTION stock_item_opening_balance() RETURNS trigger AS $$
BEGIN
    NEW.balance := COALESCE((SELECT sum(qty) FROM stock_cards WHERE outlet_id = NEW.outlet_id AND menu_item_id = NEW.menu_item_id), 0);
    RETURN NEW;
END $$ LANGUAGE plpgsql;
""",
    """
CREATE OR REPLACE FUNCTION shifts_business_day() RETURNS trigger AS $$
BEGIN
    NEW.business_day := wib_date(NEW.opened_at);
    RETURN NEW;
END $$ LANGUAGE plpgsql;
""",
    """
CREATE OR REPLACE FUNCTION orders_business_day() RETURNS trigger AS $$
BEGIN
    NEW.business_day := COALESCE(
        (SELECT s.business_day FROM shifts s WHERE s.id = NEW.cash_session_id),
        CASE WHEN TG_OP = 'UPDATE' THEN OLD.business_day END,
        wib_date(NEW.created_at)
    );
    RETURN NEW;
END $$ LANGUAGE plpgsql;
""",
    """
CREATE OR REPLACE FUNCTION expenses_business_day() RETURNS trigger AS $$
BEGIN
    NEW.business_day := COALESCE(
        (SELECT s.business_day FROM shifts s WHERE s.id = NEW.cash_session_id),
        CASE WHEN TG_OP = 'UPDATE' THEN OLD.business_day END,
        wib_date(NEW.created_at)
    );
    RETURN NEW;
END $$ LANGUAGE plpgsql;
""",
    """
CREATE OR REPLACE FUNCTION overpayments_business_day() RETURNS trigger AS $$
BEGIN
    NEW.business_day := COALESCE(
        (SELECT o.business_day FROM orders o WHERE o.id = NEW.order_id),
        (SELECT s.business_day FROM shifts s WHERE s.id = NEW.cash_session_id),
        CASE WHEN TG_OP = 'UPDATE' THEN OLD.business_day END,
        wib_date(NEW.recorded_at)
    );
    RETURN NEW;
END $$ LANGUAGE plpgsql;
""",
    """
CREATE OR REPLACE FUNCTION stock_cards_business_day() RETURNS trigger AS $$
BEGIN
    NEW.business_day := COALESCE(
        (SELECT o.business_day FROM orders o WHERE o.id = NEW.order_id),
        CASE WHEN TG_OP = 'UPDATE' THEN OLD.business_day END,
        wib_date(NEW.created_at)
    );
    RETURN NEW;
END $$ LANGUAGE plpgsql;
""",
    """
CREATE OR REPLACE FUNCTION ingredient_cards_business_day() RETURNS trigger AS $$
BEGIN
    NEW.business_day := COALESCE(
        (SELECT o.business_day FROM orders o WHERE o.id = NEW.order_id),
        (SELECT e.business_day FROM expenses e WHERE e.id = NEW.expense_id),
        CASE WHEN TG_OP = 'UPDATE' THEN OLD.business_day END,
        wib_date(NEW.created_at)
    );
    RETURN NEW;
END $$ LANGUAGE plpgsql;
""",
    """
CREATE OR REPLACE FUNCTION shifts_business_day_cascade() RETURNS trigger AS $$
BEGIN
    UPDATE orders SET business_day = NULL WHERE cash_session_id = NEW.id;
    UPDATE expenses SET business_day = NULL WHERE cash_session_id = NEW.id;
    RETURN NULL;
END $$ LANGUAGE plpgsql;
""",
    """
CREATE OR REPLACE FUNCTION orders_business_day_cascade() RETURNS trigger AS $$
BEGIN
    UPDATE overpayments SET business_day = NULL WHERE order_id = NEW.id;
    UPDATE stock_cards SET business_day = NULL WHERE order_id = NEW.id;
    UPDATE ingredient_cards SET business_day = NULL WHERE order_id = NEW.id;
    RETURN NULL;
END $$ LANGUAGE plpgsql;
""",
    """
CREATE OR REPLACE FUNCTION expenses_business_day_cascade() RETURNS trigger AS $$
BEGIN
    UPDATE ingredient_cards SET business_day = NULL WHERE expense_id = NEW.id AND order_id IS NULL;
    RETURN NULL;
END $$ LANGUAGE plpgsql;
""",
    """
CREATE OR REPLACE FUNCTION orders_money_late() RETURNS trigger AS $$
DECLARE
    row orders%ROWTYPE;
BEGIN
    SELECT * INTO row FROM orders WHERE id = NEW.id;
    IF FOUND AND money_change_late(row.cash_session_id, row.business_day) THEN
        PERFORM money_change_write(row.outlet_id, row.business_day, 'order', row.id, row.cash_session_id, row.receipt_number, 'late', 0,
            CASE WHEN row.voided_at IS NULL THEN row.total ELSE 0 END, ARRAY['total']);
    END IF;
    RETURN NULL;
END $$ LANGUAGE plpgsql;
""",
    """
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
        PERFORM money_change_write(OLD.outlet_id, OLD.business_day, 'order', OLD.id, OLD.cash_session_id, OLD.receipt_number, 'delete', old_amount, 0, ARRAY['total']);
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
    PERFORM money_change_compare('order', NEW.id, NEW.cash_session_id, NEW.receipt_number, OLD.outlet_id, OLD.business_day, old_amount,
        NEW.outlet_id, NEW.business_day, new_amount, verb, changed);
    RETURN NULL;
END $$ LANGUAGE plpgsql;
""",
    """
CREATE OR REPLACE FUNCTION expenses_money_late() RETURNS trigger AS $$
DECLARE
    row expenses%ROWTYPE;
BEGIN
    SELECT * INTO row FROM expenses WHERE id = NEW.id;
    IF FOUND AND money_change_late(row.cash_session_id, row.business_day) THEN
        PERFORM money_change_write(row.outlet_id, row.business_day, 'expense', row.id, row.cash_session_id, row.item_name, 'late', 0, row.amount, ARRAY['amount']);
    END IF;
    RETURN NULL;
END $$ LANGUAGE plpgsql;
""",
    """
CREATE OR REPLACE FUNCTION expenses_money_change() RETURNS trigger AS $$
DECLARE
    changed TEXT[] := '{}';
BEGIN
    IF money_change_fresh(TG_TABLE_NAME, OLD.id) THEN
        RETURN NULL;
    END IF;
    IF TG_OP = 'DELETE' THEN
        PERFORM money_change_write(OLD.outlet_id, OLD.business_day, 'expense', OLD.id, OLD.cash_session_id, OLD.item_name, 'delete', OLD.amount, 0, ARRAY['amount']);
        RETURN NULL;
    END IF;
    IF OLD.amount IS DISTINCT FROM NEW.amount THEN changed := array_append(changed, 'amount'::text); END IF;
    IF OLD.fund_source IS DISTINCT FROM NEW.fund_source THEN changed := array_append(changed, 'fund_source'::text); END IF;
    IF OLD.outlet_id IS DISTINCT FROM NEW.outlet_id THEN changed := array_append(changed, 'outlet'::text); END IF;
    IF OLD.business_day IS DISTINCT FROM NEW.business_day THEN changed := array_append(changed, 'business_day'::text); END IF;
    PERFORM money_change_compare('expense', NEW.id, COALESCE(NEW.cash_session_id, OLD.cash_session_id), NEW.item_name, OLD.outlet_id, OLD.business_day, OLD.amount,
        NEW.outlet_id, NEW.business_day, NEW.amount, 'update', changed);
    RETURN NULL;
END $$ LANGUAGE plpgsql;
""",
    """
CREATE OR REPLACE FUNCTION overpayments_money_late() RETURNS trigger AS $$
DECLARE
    row overpayments%ROWTYPE;
BEGIN
    SELECT * INTO row FROM overpayments WHERE id = NEW.id;
    IF FOUND AND money_change_late(row.cash_session_id, row.business_day) THEN
        PERFORM money_change_write(row.outlet_id, row.business_day, 'overpayment', row.id, row.cash_session_id, row.method_label, 'late', 0, row.amount, ARRAY['amount']);
    END IF;
    RETURN NULL;
END $$ LANGUAGE plpgsql;
""",
    """
CREATE OR REPLACE FUNCTION overpayments_money_change() RETURNS trigger AS $$
DECLARE
    changed TEXT[] := '{}';
BEGIN
    IF money_change_fresh(TG_TABLE_NAME, OLD.id) THEN
        RETURN NULL;
    END IF;
    IF TG_OP = 'DELETE' THEN
        PERFORM money_change_write(OLD.outlet_id, OLD.business_day, 'overpayment', OLD.id, OLD.cash_session_id, OLD.method_label, 'delete', OLD.amount, 0, ARRAY['amount']);
        RETURN NULL;
    END IF;
    IF OLD.amount IS DISTINCT FROM NEW.amount THEN changed := array_append(changed, 'amount'::text); END IF;
    IF OLD.outlet_id IS DISTINCT FROM NEW.outlet_id THEN changed := array_append(changed, 'outlet'::text); END IF;
    IF OLD.business_day IS DISTINCT FROM NEW.business_day THEN changed := array_append(changed, 'business_day'::text); END IF;
    PERFORM money_change_compare('overpayment', NEW.id, NEW.cash_session_id, NEW.method_label, OLD.outlet_id, OLD.business_day, OLD.amount,
        NEW.outlet_id, NEW.business_day, NEW.amount, 'update', changed);
    RETURN NULL;
END $$ LANGUAGE plpgsql;
""",
    """
CREATE OR REPLACE FUNCTION shifts_money_change() RETURNS trigger AS $$
DECLARE
    changed TEXT[] := '{}';
BEGIN
    IF TG_OP = 'DELETE' THEN
        PERFORM money_change_write(OLD.outlet_id, OLD.business_day, 'session', OLD.id, OLD.id, OLD.shift_code, 'delete', COALESCE(OLD.actual_cash, 0), 0, ARRAY['actual_cash']);
        RETURN NULL;
    END IF;
    IF OLD.status IS DISTINCT FROM 'CLOSED' THEN
        RETURN NULL;
    END IF;
    IF OLD.opening_cash IS DISTINCT FROM NEW.opening_cash THEN changed := array_append(changed, 'opening_cash'::text); END IF;
    IF OLD.actual_cash IS DISTINCT FROM NEW.actual_cash THEN changed := array_append(changed, 'actual_cash'::text); END IF;
    IF OLD.difference IS DISTINCT FROM NEW.difference THEN changed := array_append(changed, 'difference'::text); END IF;
    IF OLD.outlet_id IS DISTINCT FROM NEW.outlet_id THEN changed := array_append(changed, 'outlet'::text); END IF;
    IF OLD.business_day IS DISTINCT FROM NEW.business_day THEN changed := array_append(changed, 'business_day'::text); END IF;
    PERFORM money_change_compare('session', NEW.id, NEW.id, NEW.shift_code, OLD.outlet_id, OLD.business_day, COALESCE(OLD.actual_cash, 0),
        NEW.outlet_id, NEW.business_day, COALESCE(NEW.actual_cash, 0), 'update', changed);
    RETURN NULL;
END $$ LANGUAGE plpgsql;
""",
)

# (name, table, timing and condition, function)
TRIGGERS = (
    ('ingredient_card_balance', 'ingredient_cards', 'AFTER INSERT OR DELETE OR UPDATE OF ingredient_id, qty', 'ingredient_card_balance()'),
    ('stock_card_balance', 'stock_cards', 'AFTER INSERT OR DELETE OR UPDATE OF outlet_id, menu_item_id, qty', 'stock_card_balance()'),
    ('stock_item_opening_balance', 'stock_items', 'BEFORE INSERT OR UPDATE OF outlet_id, menu_item_id', 'stock_item_opening_balance()'),
    ('overpayments_business_day', 'overpayments', 'BEFORE INSERT OR UPDATE', 'overpayments_business_day()'),
    ('stock_cards_business_day', 'stock_cards', 'BEFORE INSERT OR UPDATE', 'stock_cards_business_day()'),
    ('ingredient_cards_business_day', 'ingredient_cards', 'BEFORE INSERT OR UPDATE', 'ingredient_cards_business_day()'),
    ('overpayments_money_mark', 'overpayments', 'AFTER INSERT', 'money_change_mark()'),
    ('overpayments_money_change', 'overpayments', 'AFTER UPDATE OR DELETE', 'overpayments_money_change()'),
)
# The late-entry check fires at commit, so it is a deferred constraint trigger.
LATE_TRIGGER = ('overpayments_money_late', 'overpayments', 'overpayments_money_late()')

# Words that must not survive in any function of the schema.
STALE_WORDS = tuple(sorted({*TABLES, *ENUMS, 'saldo', 'nomor_nota', 'nama_item', 'jumlah', 'metode_label', 'kode_shift', 'uang_aktual', 'modal_awal', 'selisih', 'sumber_dana', 'start_time'}, key=len, reverse=True))


# ---- renaming --------------------------------------------------------------------------------------------------------------------------------


def _quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _table_exists(bind, name: str) -> bool:
    return bind.scalar(sa.text("SELECT to_regclass(quote_ident(current_schema()) || '.' || :n) IS NOT NULL"), {'n': _quote(name)})


def _columns_of(bind, table: str) -> set[str]:
    rows = bind.execute(sa.text("SELECT column_name FROM information_schema.columns WHERE table_schema = current_schema() AND table_name = :t"), {'t': table})
    return {row[0] for row in rows}


def _rename_enums(bind) -> None:
    for old, new in ENUMS.items():
        has_old = bind.scalar(sa.text("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = :n AND typnamespace = current_schema()::regnamespace)"), {'n': old})
        has_new = bind.scalar(sa.text("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = :n AND typnamespace = current_schema()::regnamespace)"), {'n': new})
        if has_old and not has_new:
            op.execute(f'ALTER TYPE {_quote(old)} RENAME TO {_quote(new)}')


def _rename_tables_and_columns(bind) -> None:
    for old, new in TABLES.items():
        if _table_exists(bind, old) and not _table_exists(bind, new):
            op.execute(f'ALTER TABLE {_quote(old)} RENAME TO {_quote(new)}')
    for old_table, pairs in COLUMNS.items():
        table = TABLES.get(old_table, old_table)
        if not _table_exists(bind, table):
            continue
        present = _columns_of(bind, table)
        for old, new in pairs.items():
            if old in present and new not in present:
                op.execute(f'ALTER TABLE {_quote(table)} RENAME COLUMN {_quote(old)} TO {_quote(new)}')
                present.discard(old)
                present.add(new)


# The reverse maps, by NEW table name, to know what an object used to be called.
OLD_TABLE_OF = {new: old for old, new in TABLES.items()}
OLD_COLUMN_OF = {TABLES.get(old_table, old_table): {new: old for old, new in pairs.items()} for old_table, pairs in COLUMNS.items()}
NEW_COLUMN_OF = {TABLES.get(old_table, old_table): dict(pairs) for old_table, pairs in COLUMNS.items()}


def _retoken(name: str, table: str) -> str:
    """Swaps the old table and column words inside a name for the new ones; a word is bounded by anything that is not a letter or digit."""
    old_table = OLD_TABLE_OF.get(table, table)
    swaps = [(old_table, table)] if old_table != table else []
    swaps += list(NEW_COLUMN_OF.get(table, {}).items())
    # A name built from a column's stem ("bahan" for bahan_id) is swapped too.
    for old, new in NEW_COLUMN_OF.get(table, {}).items():
        if old.endswith('_id') and new.endswith('_id') and (old[:-3], new[:-3]) not in swaps:
            swaps.append((old[:-3], new[:-3]))
    swaps.sort(key=lambda pair: len(pair[0]), reverse=True)
    marks = {}
    for index, (old, new) in enumerate(swaps):
        mark = f'<<{index}>>'
        replaced = re.sub(rf'(?<![A-Za-z0-9]){re.escape(old)}(?![A-Za-z0-9])', mark, name)
        if replaced != name:
            marks[mark] = new
            name = replaced
    for mark, new in marks.items():
        name = name.replace(mark, new)
    return name


def _fit(old: str, new: str, taken: set[str], skipped: list[str]) -> str | None:
    """The name to use, or None when there is nothing to do or it cannot be done safely."""
    if new == old:
        return None
    if len(new) > MAX_NAME_LENGTH or new in taken:
        skipped.append(f'{old} -> {new}')
        return None
    return new


CONSTRAINTS_SQL = """
SELECT c.conname::text, c.contype::text, t.relname::text, r.relname::text,
       ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS k(num, ord)
             JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k.num ORDER BY k.ord)
FROM pg_constraint c
JOIN pg_class t ON t.oid = c.conrelid
LEFT JOIN pg_class r ON r.oid = c.confrelid
WHERE t.relnamespace = current_schema()::regnamespace AND c.contype IN ('p', 'f', 'u', 'c')
"""

INDEXES_SQL = """
SELECT ic.relname::text, t.relname::text,
       ARRAY(SELECT a.attname::text FROM unnest(i.indkey::int2[]) WITH ORDINALITY AS k(num, ord)
             JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = k.num WHERE k.num > 0 ORDER BY k.ord)
FROM pg_index i
JOIN pg_class ic ON ic.oid = i.indexrelid
JOIN pg_class t ON t.oid = i.indrelid
WHERE t.relnamespace = current_schema()::regnamespace
  AND NOT EXISTS (SELECT 1 FROM pg_constraint c WHERE c.conindid = i.indexrelid)
"""


def _old_columns(table: str, columns: list[str]) -> list[str]:
    reverse = OLD_COLUMN_OF.get(table, {})
    return [reverse.get(column, column) for column in columns]


def _rename_constraints_and_indexes(bind) -> list[str]:
    skipped: list[str] = []
    taken = {row[0] for row in bind.execute(sa.text("SELECT relname::text FROM pg_class WHERE relnamespace = current_schema()::regnamespace"))}
    taken |= {row[0] for row in bind.execute(sa.text("SELECT conname::text FROM pg_constraint c JOIN pg_class t ON t.oid = c.conrelid WHERE t.relnamespace = current_schema()::regnamespace"))}

    for name, kind, table, target, columns in bind.execute(sa.text(CONSTRAINTS_SQL)).all():
        old_table = OLD_TABLE_OF.get(table, table)
        old_columns = _old_columns(table, columns)
        if kind == 'p':
            new = f'pk_{table}' if name == f'pk_{old_table}' else _retoken(name, table)
        elif kind == 'f' and target is not None:
            old_target = OLD_TABLE_OF.get(target, target)
            expected = f'fk_{old_table}_{old_columns[0]}_{old_target}'
            new = f'fk_{table}_{columns[0]}_{target}' if name == expected else _retoken(name, table)
        else:
            new = _retoken(name, table)
        chosen = _fit(name, new, taken, skipped)
        if chosen:
            op.execute(f'ALTER TABLE {_quote(table)} RENAME CONSTRAINT {_quote(name)} TO {_quote(chosen)}')
            taken.discard(name)
            taken.add(chosen)

    for name, table, columns in bind.execute(sa.text(INDEXES_SQL)).all():
        old_table = OLD_TABLE_OF.get(table, table)
        old_columns = _old_columns(table, columns)
        expected = f'index_{old_table}_on_' + '_and_'.join(old_columns)
        new = f'index_{table}_on_' + '_and_'.join(columns) if columns and name == expected else _retoken(name, table)
        chosen = _fit(name, new, taken, skipped)
        if chosen:
            op.execute(f'ALTER INDEX {_quote(name)} RENAME TO {_quote(chosen)}')
            taken.discard(name)
            taken.add(chosen)
    return skipped


# ---- the check -------------------------------------------------------------------------------------------------------------------------------


def _verify(bind) -> None:
    missing = [new for new in TABLES.values() if not _table_exists(bind, new)]
    if missing:
        raise RuntimeError(f'tables that should exist are missing: {", ".join(sorted(missing))}')
    absent = []
    for old_table, pairs in COLUMNS.items():
        table = TABLES.get(old_table, old_table)
        present = _columns_of(bind, table)
        absent += [f'{table}.{new}' for new in pairs.values() if new not in present]
    if absent:
        raise RuntimeError(f'columns that should exist are missing: {", ".join(sorted(absent))}')
    pattern = r'\m(' + '|'.join(re.escape(word) for word in STALE_WORDS) + r')\M'
    stale = [row[0] for row in bind.execute(sa.text("SELECT proname::text FROM pg_proc WHERE pronamespace = current_schema()::regnamespace AND prosrc ~ :p ORDER BY 1"), {'p': pattern})]
    if stale:
        raise RuntimeError(f'functions that still mention an old name: {", ".join(stale)}')


def upgrade() -> None:
    bind = op.get_bind()
    op.execute("SET LOCAL lock_timeout = '5s'")

    # Nothing may fire while names are half changed.
    for name, table in OLD_TRIGGERS:
        op.execute(f'DROP TRIGGER IF EXISTS {_quote(name)} ON {_quote(table)}')

    _rename_enums(bind)
    _rename_tables_and_columns(bind)
    skipped = _rename_constraints_and_indexes(bind)

    for function in FUNCTIONS:
        op.execute(function)
    for name, table, timing, function in TRIGGERS:
        op.execute(f'DROP TRIGGER IF EXISTS {_quote(name)} ON {_quote(table)}')
        op.execute(f'CREATE TRIGGER {_quote(name)} {timing} ON {_quote(table)} FOR EACH ROW EXECUTE FUNCTION {function}')
    name, table, function = LATE_TRIGGER
    op.execute(f'DROP TRIGGER IF EXISTS {_quote(name)} ON {_quote(table)}')
    op.execute(f'CREATE CONSTRAINT TRIGGER {_quote(name)} AFTER INSERT ON {_quote(table)} DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION {function}')
    for function in OLD_FUNCTIONS:
        op.execute(f'DROP FUNCTION IF EXISTS {function}')

    _verify(bind)
    if skipped:
        log.warning('names kept as they were (too long or already taken): %s', '; '.join(skipped))


def downgrade() -> None:
    # The old names are not restored: the code no longer knows them, and a mistake after release is fixed with a forward migration.
    pass
