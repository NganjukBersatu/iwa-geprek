"""tugas rutin: jenis tugas, kode shift, penerima, pengisi per orang, dan pola berulang; pembersihan tujuh izin tanpa fitur (ulasan, kelola pelanggan, hapus pelanggan, hapus kunjungan, kelola mitra), dan batas panjang CHECK untuk kolom teks tabel stasiun, absen, hitung stok, dan lainnya

Revision ID: e7a9c1d3f5b8
Revises: d6f8b0c2e4a9
Create Date: 2026-11-17 16:00:00.000000

Pembersihan izin ulasan hanya membuang kunci dari roles.permissions; Down tidak mengembalikannya karena kunci itu tidak pernah dipakai fitur apa pun.
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'e7a9c1d3f5b8'
down_revision: Union[str, Sequence[str], None] = 'd6f8b0c2e4a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")

# Kolom baru bernilai bawaan yang sama dengan perilaku lama dan tabel baru kosong, jadi jumlah baris dan uang tidak berubah.
STATEMENTS = (
    "ALTER TABLE outlet_batches ADD COLUMN IF NOT EXISTS kind TEXT NOT NULL DEFAULT 'outlet'",
    "ALTER TABLE outlet_batches ADD COLUMN IF NOT EXISTS fill_mode TEXT NOT NULL DEFAULT 'one'",
    "ALTER TABLE outlet_batches DROP CONSTRAINT IF EXISTS check_outlet_batches_kind_values",
    "ALTER TABLE outlet_batches ADD CONSTRAINT check_outlet_batches_kind_values CHECK (kind IN ('outlet', 'routine')) NOT VALID",
    "ALTER TABLE outlet_batches VALIDATE CONSTRAINT check_outlet_batches_kind_values",
    "ALTER TABLE outlet_batches DROP CONSTRAINT IF EXISTS check_outlet_batches_fill_mode_values",
    "ALTER TABLE outlet_batches ADD CONSTRAINT check_outlet_batches_fill_mode_values"
    " CHECK (fill_mode IN ('one', 'each') AND (kind = 'routine' OR fill_mode = 'one')) NOT VALID",
    "ALTER TABLE outlet_batches VALIDATE CONSTRAINT check_outlet_batches_fill_mode_values",
    # Pola berulang: tiap N hari, minggu, atau bulan dihitung dari starts_on; satuan kosong berarti templat lama yang masih memakai weekdays.
    "ALTER TABLE outlet_batches ADD COLUMN IF NOT EXISTS repeat_unit TEXT",
    "ALTER TABLE outlet_batches ADD COLUMN IF NOT EXISTS repeat_every INTEGER NOT NULL DEFAULT 1",
    "ALTER TABLE outlet_batches ADD COLUMN IF NOT EXISTS starts_on DATE",
    "ALTER TABLE outlet_batches DROP CONSTRAINT IF EXISTS check_outlet_batches_repeat_values",
    "ALTER TABLE outlet_batches ADD CONSTRAINT check_outlet_batches_repeat_values CHECK ("
    "(repeat_unit IS NULL OR repeat_unit IN ('day', 'week', 'month'))"
    " AND repeat_every BETWEEN 1 AND 365"
    " AND (repeat_unit IS NULL OR starts_on IS NOT NULL)) NOT VALID",
    "ALTER TABLE outlet_batches VALIDATE CONSTRAINT check_outlet_batches_repeat_values",
    "CREATE INDEX IF NOT EXISTS index_outlet_batches_on_outlet_id_and_kind ON outlet_batches (outlet_id, kind)",
    # Penerima tugas rutin: semua yang dijadwalkan di kode shiftnya, atau orang-orang tertentu.
    "ALTER TABLE outlet_batches ADD COLUMN IF NOT EXISTS target TEXT NOT NULL DEFAULT 'shift'",
    "ALTER TABLE outlet_batches DROP CONSTRAINT IF EXISTS check_outlet_batches_target_values",
    "ALTER TABLE outlet_batches ADD CONSTRAINT check_outlet_batches_target_values"
    " CHECK (target IN ('shift', 'staff') AND (kind = 'routine' OR target = 'shift')) NOT VALID",
    "ALTER TABLE outlet_batches VALIDATE CONSTRAINT check_outlet_batches_target_values",
    "CREATE TABLE IF NOT EXISTS outlet_batch_staff ("
    " batch_id VARCHAR NOT NULL,"
    " staff_id VARCHAR NOT NULL,"
    " CONSTRAINT pk_outlet_batch_staff PRIMARY KEY (batch_id, staff_id))",
    "CREATE INDEX IF NOT EXISTS index_outlet_batch_staff_on_staff_id ON outlet_batch_staff (staff_id)",
    "ALTER TABLE outlet_batch_staff DROP CONSTRAINT IF EXISTS fk_outlet_batch_staff_batch_id_outlet_batches",
    "ALTER TABLE outlet_batch_staff ADD CONSTRAINT fk_outlet_batch_staff_batch_id_outlet_batches"
    " FOREIGN KEY (batch_id) REFERENCES outlet_batches (id) ON DELETE CASCADE",
    "ALTER TABLE outlet_batch_staff DROP CONSTRAINT IF EXISTS fk_outlet_batch_staff_staff_id_staff",
    "ALTER TABLE outlet_batch_staff ADD CONSTRAINT fk_outlet_batch_staff_staff_id_staff"
    " FOREIGN KEY (staff_id) REFERENCES staff (id) ON DELETE CASCADE",
    "CREATE TABLE IF NOT EXISTS outlet_batch_shift_codes ("
    " batch_id VARCHAR NOT NULL,"
    " shift_code_id VARCHAR NOT NULL,"
    " CONSTRAINT pk_outlet_batch_shift_codes PRIMARY KEY (batch_id, shift_code_id))",
    "CREATE INDEX IF NOT EXISTS index_outlet_batch_shift_codes_on_shift_code_id ON outlet_batch_shift_codes (shift_code_id)",
    "ALTER TABLE outlet_batch_shift_codes DROP CONSTRAINT IF EXISTS fk_outlet_batch_shift_codes_batch_id_outlet_batches",
    "ALTER TABLE outlet_batch_shift_codes ADD CONSTRAINT fk_outlet_batch_shift_codes_batch_id_outlet_batches"
    " FOREIGN KEY (batch_id) REFERENCES outlet_batches (id) ON DELETE CASCADE",
    "ALTER TABLE outlet_batch_shift_codes DROP CONSTRAINT IF EXISTS fk_outlet_batch_shift_codes_shift_code_id_shift_codes",
    "ALTER TABLE outlet_batch_shift_codes ADD CONSTRAINT fk_outlet_batch_shift_codes_shift_code_id_shift_codes"
    " FOREIGN KEY (shift_code_id) REFERENCES shift_codes (id) ON DELETE CASCADE",
    # Kosong untuk tugas yang cukup diisi satu orang, id staf untuk tugas yang diisi tiap orang.
    "ALTER TABLE outlet_batch_runs ADD COLUMN IF NOT EXISTS filler_key VARCHAR(64) NOT NULL DEFAULT ''",
    "CREATE UNIQUE INDEX IF NOT EXISTS unique_outlet_batch_runs_batch_id_and_day_and_filler_key"
    " ON outlet_batch_runs (batch_id, day, filler_key)",
    "ALTER TABLE outlet_batch_runs DROP CONSTRAINT IF EXISTS uq_outlet_batch_runs_batch_day",
    # Tugas tindak lanjut menunjuk pengisian asalnya; pengisian yang dihapus hanya mengosongkan rujukan, tugasnya tetap ada.
    "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS source_run_id VARCHAR",
    "CREATE INDEX IF NOT EXISTS index_tasks_on_source_run_id ON tasks (source_run_id)",
    "ALTER TABLE tasks DROP CONSTRAINT IF EXISTS fk_tasks_source_run_id_outlet_batch_runs",
    "ALTER TABLE tasks ADD CONSTRAINT fk_tasks_source_run_id_outlet_batch_runs"
    " FOREIGN KEY (source_run_id) REFERENCES outlet_batch_runs (id) ON DELETE SET NULL NOT VALID",
    "ALTER TABLE tasks VALIDATE CONSTRAINT fk_tasks_source_run_id_outlet_batch_runs",
    # Pengisian yang dibatalkan pengisinya tetap disimpan dengan tanda batal.
    "ALTER TABLE outlet_batch_runs ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMPTZ",
    "ALTER TABLE outlet_batch_runs ADD COLUMN IF NOT EXISTS cancelled_by_id VARCHAR",
    "CREATE INDEX IF NOT EXISTS index_outlet_batch_runs_on_cancelled_by_id ON outlet_batch_runs (cancelled_by_id)",
    "ALTER TABLE outlet_batch_runs DROP CONSTRAINT IF EXISTS fk_outlet_batch_runs_cancelled_by_id_staff",
    "ALTER TABLE outlet_batch_runs ADD CONSTRAINT fk_outlet_batch_runs_cancelled_by_id_staff"
    " FOREIGN KEY (cancelled_by_id) REFERENCES staff (id) ON DELETE SET NULL NOT VALID",
    "ALTER TABLE outlet_batch_runs VALIDATE CONSTRAINT fk_outlet_batch_runs_cancelled_by_id_staff",
    # Isi lama tiap pengisian sebelum diperbaiki atau dibatalkan.
    "CREATE TABLE IF NOT EXISTS outlet_batch_run_versions ("
    " completed_at TIMESTAMPTZ NOT NULL, changed_at TIMESTAMPTZ NOT NULL DEFAULT now(), number INTEGER NOT NULL,"
    " id VARCHAR NOT NULL, run_id VARCHAR NOT NULL, action VARCHAR(10) NOT NULL, completed_by_id VARCHAR, changed_by_id VARCHAR,"
    " answers JSONB NOT NULL,"
    " CONSTRAINT pk_outlet_batch_run_versions PRIMARY KEY (id),"
    " CONSTRAINT check_outlet_batch_run_versions_action_values CHECK (action IN ('fix', 'cancel', 'delete')))",
    "CREATE UNIQUE INDEX IF NOT EXISTS unique_outlet_batch_run_versions_run_id_and_number ON outlet_batch_run_versions (run_id, number)",
    "CREATE INDEX IF NOT EXISTS index_outlet_batch_run_versions_on_completed_by_id ON outlet_batch_run_versions (completed_by_id)",
    "CREATE INDEX IF NOT EXISTS index_outlet_batch_run_versions_on_changed_by_id ON outlet_batch_run_versions (changed_by_id)",
    "ALTER TABLE outlet_batch_run_versions DROP CONSTRAINT IF EXISTS fk_outlet_batch_run_versions_run_id_outlet_batch_runs",
    "ALTER TABLE outlet_batch_run_versions ADD CONSTRAINT fk_outlet_batch_run_versions_run_id_outlet_batch_runs"
    " FOREIGN KEY (run_id) REFERENCES outlet_batch_runs (id) ON DELETE CASCADE",
    "ALTER TABLE outlet_batch_run_versions DROP CONSTRAINT IF EXISTS fk_outlet_batch_run_versions_completed_by_id_staff",
    "ALTER TABLE outlet_batch_run_versions ADD CONSTRAINT fk_outlet_batch_run_versions_completed_by_id_staff"
    " FOREIGN KEY (completed_by_id) REFERENCES staff (id) ON DELETE SET NULL",
    "ALTER TABLE outlet_batch_run_versions DROP CONSTRAINT IF EXISTS fk_outlet_batch_run_versions_changed_by_id_staff",
    "ALTER TABLE outlet_batch_run_versions ADD CONSTRAINT fk_outlet_batch_run_versions_changed_by_id_staff"
    " FOREIGN KEY (changed_by_id) REFERENCES staff (id) ON DELETE SET NULL",
    # Stasiun aktif cabang dihitung ulang dari tablet terdaftar yang memegangnya: tablet yang dipasangkan sebelum perbaikan sync_used tidak menyalakan stasiunnya.
    # Idempoten, dan baris yang sudah benar (termasuk yang disetel tangan) tidak berubah.
    "INSERT INTO station_branch_settings (outlet_id, station_id, used, reminder_seconds)"
    " SELECT DISTINCT d.outlet_id, ds.station_id, TRUE, 60 FROM device_stations ds JOIN devices d ON d.id = ds.device_id"
    " WHERE d.status = 'terdaftar' ON CONFLICT (outlet_id, station_id) DO NOTHING",
    "UPDATE station_branch_settings s SET used = EXISTS ("
    " SELECT 1 FROM device_stations ds JOIN devices d ON d.id = ds.device_id"
    " WHERE d.outlet_id = s.outlet_id AND ds.station_id = s.station_id AND d.status = 'terdaftar')"
    " WHERE s.used IS DISTINCT FROM EXISTS ("
    " SELECT 1 FROM device_stations ds JOIN devices d ON d.id = ds.device_id"
    " WHERE d.outlet_id = s.outlet_id AND ds.station_id = s.station_id AND d.status = 'terdaftar')",
    # Pesanan tidak boleh kehilangan metode bayar, promo, penyetuju batal, kategori pengunjung, gender, atau catatannya diam-diam (aturan 4.4.3): SET NULL jadi RESTRICT.
    # Kunci asing baru dibuat lebih dulu dan divalidasi, baru yang lama dibuang (aturan 4.4.5); nama tujuan dibaca dari katalog.
    """DO $$ DECLARE old RECORD; BEGIN
    FOR old IN
        SELECT k.conname, a.attname AS column_name, k.confrelid::regclass::text AS parent
        FROM pg_constraint k JOIN pg_attribute a ON a.attrelid = k.conrelid AND a.attnum = k.conkey[1]
        WHERE k.contype = 'f' AND k.conrelid = 'orders'::regclass AND array_length(k.conkey, 1) = 1 AND k.confdeltype = 'n'
          AND a.attname IN ('payment_method_id', 'promo_id', 'voided_by_id', 'visitor_category_id', 'visitor_gender_id', 'note_id')
    LOOP
        EXECUTE format('ALTER TABLE orders ADD CONSTRAINT %I FOREIGN KEY (%I) REFERENCES %s (id) ON DELETE RESTRICT NOT VALID', 'tmp_' || old.conname, old.column_name, old.parent);
        EXECUTE format('ALTER TABLE orders VALIDATE CONSTRAINT %I', 'tmp_' || old.conname);
        EXECUTE format('ALTER TABLE orders DROP CONSTRAINT %I', old.conname);
        EXECUTE format('ALTER TABLE orders RENAME CONSTRAINT %I TO %I', 'tmp_' || old.conname, old.conname);
    END LOOP;
    END $$""",
    # Tiga izin ulasan dan empat izin pelanggan dan mitra tidak punya fitur dan dibuang dari katalog; peran yang menyimpannya dibersihkan, urutan kunci lain tetap.
    "UPDATE roles SET permissions = ("
    " SELECT COALESCE(jsonb_agg(element.key ORDER BY element.position), '[]'::jsonb)"
    " FROM jsonb_array_elements(roles.permissions::jsonb) WITH ORDINALITY AS element(key, position)"
    " WHERE element.key #>> '{}' NOT IN ('ulasan.lihat', 'ulasan.sinkron', 'ulasan.hapus', 'pelanggan.kelola', 'pelanggan.hapus', 'kunjungan.hapus', 'mitra.kelola'))::json"
    " WHERE jsonb_typeof(permissions::jsonb) = 'array'"
    " AND permissions::jsonb ?| ARRAY['ulasan.lihat', 'ulasan.sinkron', 'ulasan.hapus', 'pelanggan.kelola', 'pelanggan.hapus', 'kunjungan.hapus', 'mitra.kelola']",
)


# Batas panjang kolom teks lewat CHECK (aturan 4.3.2): id dan rujukan 64, nilai pilihan 32, dan teks bebas sebesar batas yang sudah ditegakkan kodenya.
LENGTH_LIMITS = {
    "attendance_clock_events": {"id": 64, "staff_id": 64, "attendance_id": 64, "idempotency_key": 64, "kind": 32, "time_source": 32, "request_hash": 64},
    "branch_periods": {"id": 64, "outlet_id": 64},
    "categories": {"outlet_id": 64, "created_by_id": 64, "shift_kind": 32, "shift_start_from": 32, "shift_start_until": 32},
    "category_branch_stations": {"outlet_id": 64, "category_id": 64, "station_id": 64},
    "category_stations": {"category_id": 64, "station_id": 64},
    "device_printers": {"id": 64, "device_id": 64, "printer_slot": 32, "station_id": 64, "printer_name": 120, "printer_address": 64, "connection": 32},
    "device_station_prints": {"device_id": 64, "station_id": 64},
    "device_stations": {"device_id": 64, "station_id": 64},
    "ingredient_count_changes": {"id": 64, "outlet_id": 64, "count_id": 64, "ingredient_id": 64, "staff_id": 64, "ingredient_name": 255, "action": 32},
    "ingredient_count_drafts": {"outlet_id": 64, "ingredient_id": 64, "staff_id": 64},
    "ingredient_count_requests": {"id": 64, "outlet_id": 64, "status": 32, "note": 255, "requested_by": 64, "decided_by": 64, "count_id": 64, "seen_by": 64},
    "ingredient_counts": {"source": 32},
    "menu_branch_targets": {"outlet_id": 64, "menu_item_id": 64},
    "menu_outlet_costs": {"menu_item_id": 64, "outlet_id": 64},
    "menu_targets": {"menu_item_id": 64},
    "money_changes": {"id": 64, "outlet_id": 64, "subject": 32, "subject_id": 64, "session_id": 64, "action": 32, "staff_id": 64},
    "outlets": {"print_mode": 32},
    "printer_categories": {"outlet_id": 64, "category_id": 64, "printer_slot": 32, "created_by": 64},
    "release_reads": {"staff_id": 64, "surface": 32, "version": 64},
    "roles": {"station_id": 64, "created_by": 64},
    "sop_reads": {"sop_id": 64, "staff_id": 64},
    "station_branch_roles": {"outlet_id": 64, "station_id": 64, "role_id": 64},
    "station_branch_settings": {"outlet_id": 64, "station_id": 64},
    "station_flows": {"outlet_id": 64},
    "station_menu_stats": {"id": 64, "outlet_id": 64, "station_id": 64, "menu_item_id": 64, "menu_name": 255},
    "station_roles": {"station_id": 64, "role_id": 64},
    "station_staff_stats": {"id": 64, "outlet_id": 64, "station_id": 64, "staff_id": 64},
    "station_task_steps": {"id": 64, "task_id": 64, "step": 32, "staff_id": 64, "reason": 255},
    "station_tasks": {"id": 64, "order_id": 64, "order_item_id": 64, "outlet_id": 64, "station_id": 64, "started_by": 64, "finished_by": 64, "correction": 32, "removed_label": 300, "hold_reason": 255, "held_by": 64},
    "stations": {"id": 64, "name": 40, "kind": 32},
}


def _length_checks() -> list[str]:
    statements: list[str] = []
    for table, columns in LENGTH_LIMITS.items():
        for column, limit in columns.items():
            name = f'check_{table}_{column}_length'
            statements += [
                f'ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {name}',
                f'ALTER TABLE {table} ADD CONSTRAINT {name} CHECK (char_length({column}) <= {limit}) NOT VALID',
                f'ALTER TABLE {table} VALIDATE CONSTRAINT {name}',
            ]
    return statements


def upgrade() -> None:
    for statement in (*TIMEOUTS, *STATEMENTS, *_length_checks()):
        op.execute(statement)


def downgrade() -> None:
    """Pengisian per orang dihapus dulu karena aturan lama hanya mengizinkan satu pengisian per tugas per hari."""
    for statement in TIMEOUTS:
        op.execute(statement)
    for table, columns in LENGTH_LIMITS.items():
        for column in columns:
            op.execute(f'ALTER TABLE {table} DROP CONSTRAINT IF EXISTS check_{table}_{column}_length')
    op.execute('DROP TABLE IF EXISTS outlet_batch_run_versions')
    op.execute('DELETE FROM outlet_batch_runs WHERE cancelled_at IS NOT NULL')
    op.execute('ALTER TABLE outlet_batch_runs DROP CONSTRAINT IF EXISTS fk_outlet_batch_runs_cancelled_by_id_staff')
    op.execute('DROP INDEX IF EXISTS index_outlet_batch_runs_on_cancelled_by_id')
    for column in ('cancelled_by_id', 'cancelled_at'):
        op.execute(f'ALTER TABLE outlet_batch_runs DROP COLUMN IF EXISTS {column}')
    op.execute('ALTER TABLE tasks DROP CONSTRAINT IF EXISTS fk_tasks_source_run_id_outlet_batch_runs')
    op.execute('DROP INDEX IF EXISTS index_tasks_on_source_run_id')
    op.execute('ALTER TABLE tasks DROP COLUMN IF EXISTS source_run_id')
    op.execute("DELETE FROM outlet_batch_runs WHERE filler_key <> ''")
    op.execute('ALTER TABLE outlet_batch_runs DROP CONSTRAINT IF EXISTS uq_outlet_batch_runs_batch_day')
    op.execute('ALTER TABLE outlet_batch_runs ADD CONSTRAINT uq_outlet_batch_runs_batch_day UNIQUE (batch_id, day)')
    op.execute('DROP INDEX IF EXISTS unique_outlet_batch_runs_batch_id_and_day_and_filler_key')
    op.execute('ALTER TABLE outlet_batch_runs DROP COLUMN IF EXISTS filler_key')
    op.execute('DROP TABLE IF EXISTS outlet_batch_shift_codes')
    op.execute('DROP TABLE IF EXISTS outlet_batch_staff')
    op.execute('DROP INDEX IF EXISTS index_outlet_batches_on_outlet_id_and_kind')
    for constraint in ('check_outlet_batches_target_values', 'check_outlet_batches_repeat_values', 'check_outlet_batches_fill_mode_values', 'check_outlet_batches_kind_values'):
        op.execute(f'ALTER TABLE outlet_batches DROP CONSTRAINT IF EXISTS {constraint}')
    for column in ('target', 'starts_on', 'repeat_every', 'repeat_unit', 'fill_mode', 'kind'):
        op.execute(f'ALTER TABLE outlet_batches DROP COLUMN IF EXISTS {column}')
