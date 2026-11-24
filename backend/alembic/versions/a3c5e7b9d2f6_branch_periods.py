"""periode tutup buku per cabang, serta stasiun tanpa tablet, peran bawaan stasiun, dan printer per stasiun

Revision ID: a3c5e7b9d2f6
Revises: e7a9c1d3f568
Create Date: 2026-11-15 17:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'a3c5e7b9d2f6'
down_revision: Union[str, Sequence[str], None] = 'e7a9c1d3f568'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")

# Hanya periode yang diatur tangan yang disimpan; bulan lain dibentuk dari pola patokan terakhir, jadi tabel ini tetap kecil.
PERIODS = """
CREATE TABLE IF NOT EXISTS branch_periods (
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    pattern_start_day INTEGER,
    pattern_end_day INTEGER,
    id TEXT NOT NULL,
    outlet_id TEXT NOT NULL,
    CONSTRAINT pk_branch_periods PRIMARY KEY (id),
    CONSTRAINT unique_branch_periods_outlet_id_start_date UNIQUE (outlet_id, start_date),
    CONSTRAINT check_branch_periods_end_date_order CHECK (end_date >= start_date),
    CONSTRAINT check_branch_periods_pattern_days CHECK (
        (pattern_start_day IS NULL AND pattern_end_day IS NULL)
        OR (pattern_start_day BETWEEN 1 AND 31 AND pattern_end_day BETWEEN 1 AND 31)
    )
)
"""

PERIODS_FOREIGN_KEY = """
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_branch_periods_outlet_id_outlets') THEN
        ALTER TABLE branch_periods ADD CONSTRAINT fk_branch_periods_outlet_id_outlets FOREIGN KEY (outlet_id) REFERENCES outlets(id) ON DELETE RESTRICT;
    END IF;
END $$;
"""

STATION_PRINTS = """
CREATE TABLE IF NOT EXISTS device_station_prints (
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    device_id TEXT NOT NULL,
    station_id TEXT NOT NULL,
    CONSTRAINT pk_device_station_prints PRIMARY KEY (device_id, station_id)
)
"""

STATION_ROLES = """
CREATE TABLE IF NOT EXISTS station_roles (
    station_id TEXT NOT NULL,
    role_id TEXT NOT NULL,
    CONSTRAINT pk_station_roles PRIMARY KEY (station_id, role_id)
)
"""

# Kunci utama tabel baru sudah diawali kolom pertama foreign key-nya; kolom kedua diberi indeks sendiri.
INDEXES = (
    "CREATE INDEX IF NOT EXISTS index_device_station_prints_on_station_id ON device_station_prints (station_id)",
    "CREATE INDEX IF NOT EXISTS index_station_roles_on_role_id ON station_roles (role_id)",
)

FOREIGN_KEYS = """
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_device_station_prints_device_id_devices') THEN
        ALTER TABLE device_station_prints ADD CONSTRAINT fk_device_station_prints_device_id_devices FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_device_station_prints_station_id_stations') THEN
        ALTER TABLE device_station_prints ADD CONSTRAINT fk_device_station_prints_station_id_stations FOREIGN KEY (station_id) REFERENCES stations(id) ON DELETE CASCADE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_station_roles_station_id_stations') THEN
        ALTER TABLE station_roles ADD CONSTRAINT fk_station_roles_station_id_stations FOREIGN KEY (station_id) REFERENCES stations(id) ON DELETE CASCADE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_station_roles_role_id_roles') THEN
        ALTER TABLE station_roles ADD CONSTRAINT fk_station_roles_role_id_roles FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE RESTRICT;
    END IF;
END $$;
"""

# Printer kini milik stasiun: slot station membawa station_id, jadi kunci (device_id, printer_slot) diganti id sendiri dan dua indeks unik parsial.
PRINTER_STATIONS = """
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'device_printers' AND column_name = 'id') THEN
        ALTER TABLE device_printers ADD COLUMN id TEXT NOT NULL DEFAULT gen_random_uuid()::text;
        ALTER TABLE device_printers DROP CONSTRAINT pk_device_printers;
        ALTER TABLE device_printers ADD CONSTRAINT pk_device_printers PRIMARY KEY (id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'device_printers' AND column_name = 'station_id') THEN
        ALTER TABLE device_printers ADD COLUMN station_id TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'check_device_printers_station_id_slot') THEN
        ALTER TABLE device_printers ADD CONSTRAINT check_device_printers_station_id_slot CHECK (station_id IS NULL OR printer_slot = 'station');
    END IF;
END $$;
"""

PRINTER_INDEXES = (
    "CREATE UNIQUE INDEX IF NOT EXISTS unique_device_printers_device_id_printer_slot ON device_printers (device_id, printer_slot) WHERE station_id IS NULL",
    "CREATE UNIQUE INDEX IF NOT EXISTS unique_device_printers_device_id_station_id ON device_printers (device_id, station_id) WHERE station_id IS NOT NULL",
    "CREATE INDEX IF NOT EXISTS index_device_printers_on_station_id ON device_printers (station_id)",
)

PRINTER_FOREIGN_KEY = """
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_device_printers_station_id_stations') THEN
        ALTER TABLE device_printers ADD CONSTRAINT fk_device_printers_station_id_stations FOREIGN KEY (station_id) REFERENCES stations(id) ON DELETE CASCADE;
    END IF;
END $$;
"""

# Cabang Mode Kasir: slot printer Bar atau Dapur yang semua kategorinya menuju satu stasiun tanpa tablet menjadi stasiun yang dicetak dari tablet kasir.
STATION_PRINTS_FROM_CATEGORIES = """
WITH slot_station AS (
    SELECT pc.outlet_id,
           pc.printer_slot,
           min(CASE WHEN cbs.category_id IS NOT NULL THEN cbs.station_id ELSE cs.station_id END) AS station_id,
           count(DISTINCT CASE WHEN cbs.category_id IS NOT NULL THEN cbs.station_id ELSE cs.station_id END) AS stations
    FROM printer_categories pc
    LEFT JOIN category_branch_stations cbs ON cbs.outlet_id = pc.outlet_id AND cbs.category_id = pc.category_id
    LEFT JOIN category_stations cs ON cs.category_id = pc.category_id
    GROUP BY pc.outlet_id, pc.printer_slot
)
INSERT INTO device_station_prints (device_id, station_id)
SELECT d.id, ss.station_id
FROM slot_station ss
JOIN outlets o ON o.id = ss.outlet_id AND o.print_mode = 'cashier'
JOIN stations s ON s.id = ss.station_id AND s.kind = 'make'
JOIN devices d ON d.outlet_id = ss.outlet_id AND d.status = 'terdaftar'
WHERE ss.stations = 1
  AND (d.section = 'kasir' OR EXISTS (
      SELECT 1 FROM device_stations ds JOIN stations h ON h.id = ds.station_id AND h.kind = 'handover' WHERE ds.device_id = d.id
  ))
  AND NOT EXISTS (
      SELECT 1 FROM device_stations held JOIN devices holder ON holder.id = held.device_id
      WHERE held.station_id = ss.station_id AND holder.outlet_id = ss.outlet_id AND holder.status = 'terdaftar'
  )
ON CONFLICT (device_id, station_id) DO NOTHING
"""

# Stasiun aktif di cabang kini berarti dipegang tablet terdaftar; nilai lama diselaraskan sekali di sini.
# Hanya baris yang sudah ada yang diselaraskan: penjaga pra_deploy menolak jumlah baris yang berubah, dan baris yang belum ada sudah berarti tidak dipakai.
STATIONS_USED_FROM_TABLETS = """
UPDATE station_branch_settings sbs
SET used = EXISTS (
    SELECT 1 FROM device_stations ds JOIN devices d ON d.id = ds.device_id
    WHERE ds.station_id = sbs.station_id AND d.outlet_id = sbs.outlet_id AND d.status = 'terdaftar'
)
WHERE sbs.used IS DISTINCT FROM EXISTS (
    SELECT 1 FROM device_stations ds JOIN devices d ON d.id = ds.device_id
    WHERE ds.station_id = sbs.station_id AND d.outlet_id = sbs.outlet_id AND d.status = 'terdaftar'
)
"""


def upgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    # Indeks unik (outlet_id, start_date) sudah menopang foreign key dengan outlet_id di depan; tabel baru kosong sehingga kuncinya sesaat.
    op.execute(PERIODS)
    op.execute(PERIODS_FOREIGN_KEY)
    op.execute(STATION_PRINTS)
    op.execute(STATION_ROLES)
    for statement in INDEXES:
        op.execute(statement)
    op.execute(FOREIGN_KEYS)
    # device_printers hanya beberapa baris per tablet, jadi indeks biasa di dalam transaksi aman.
    op.execute(PRINTER_STATIONS)
    for statement in PRINTER_INDEXES:
        op.execute(statement)
    op.execute(PRINTER_FOREIGN_KEY)
    op.execute(STATION_PRINTS_FROM_CATEGORIES)
    op.execute(STATIONS_USED_FROM_TABLETS)


def downgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    op.execute("DELETE FROM device_printers WHERE station_id IS NOT NULL")
    op.execute("DROP INDEX IF EXISTS index_device_printers_on_station_id")
    op.execute("DROP INDEX IF EXISTS unique_device_printers_device_id_station_id")
    op.execute("DROP INDEX IF EXISTS unique_device_printers_device_id_printer_slot")
    op.execute("ALTER TABLE device_printers DROP CONSTRAINT IF EXISTS check_device_printers_station_id_slot")
    op.execute("ALTER TABLE device_printers DROP CONSTRAINT IF EXISTS fk_device_printers_station_id_stations")
    op.execute("ALTER TABLE device_printers DROP COLUMN IF EXISTS station_id")
    op.execute("ALTER TABLE device_printers DROP CONSTRAINT IF EXISTS pk_device_printers")
    op.execute("ALTER TABLE device_printers ADD CONSTRAINT pk_device_printers PRIMARY KEY (device_id, printer_slot)")
    op.execute("ALTER TABLE device_printers DROP COLUMN IF EXISTS id")
    op.execute("DROP TABLE IF EXISTS station_roles")
    op.execute("DROP TABLE IF EXISTS device_station_prints")
    op.execute("DROP TABLE IF EXISTS branch_periods")
