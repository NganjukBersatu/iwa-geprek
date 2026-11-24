"""base schema: branches, roles, accounts, devices, visitor lists and the shared enums

Revision ID: a0b1c2d3e401
Revises: (none, first revision of the chain)

The v2 chain started on top of tables owned by a legacy chain that is not in this repository, so a database built from nothing
could not be created. This revision and its three siblings create those tables, in the shape the chain expects to find them:
columns that later revisions add (roles.is_admin, expenses.bahan_id, the business_day columns, ...) are left out on purpose.

Every statement is IF NOT EXISTS, so a database that already has the tables (production, staging) is left exactly as it is.
Down is a no-op: dropping the core tables would destroy data, and a mistake after release is fixed with a forward migration.
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'a0b1c2d3e401'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

STATEMENTS = (
    """
    DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typnamespace = current_schema()::regnamespace AND typname = 'shift_status') THEN CREATE TYPE shift_status AS ENUM ('OPEN', 'CLOSED'); END IF; END $$
    """,
    """
    DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typnamespace = current_schema()::regnamespace AND typname = 'status_pengajuan_pembatalan') THEN CREATE TYPE status_pengajuan_pembatalan AS ENUM ('menunggu', 'disetujui', 'ditolak'); END IF; END $$
    """,
    """
    DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typnamespace = current_schema()::regnamespace AND typname = 'sumber_dana') THEN CREATE TYPE sumber_dana AS ENUM ('kas_laci', 'dana_lain', 'uang_belanja'); END IF; END $$
    """,
    """
    DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typnamespace = current_schema()::regnamespace AND typname = 'status_kehadiran') THEN CREATE TYPE status_kehadiran AS ENUM ('hadir', 'telat', 'izin', 'sakit', 'alfa'); END IF; END $$
    """,
    """
    DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typnamespace = current_schema()::regnamespace AND typname = 'jenis_pengajuan') THEN CREATE TYPE jenis_pengajuan AS ENUM ('izin', 'sakit'); END IF; END $$
    """,
    """
    DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typnamespace = current_schema()::regnamespace AND typname = 'status_pengajuan') THEN CREATE TYPE status_pengajuan AS ENUM ('menunggu', 'disetujui', 'ditolak'); END IF; END $$
    """,
    """
    DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typnamespace = current_schema()::regnamespace AND typname = 'jenis_tugas') THEN CREATE TYPE jenis_tugas AS ENUM ('penugasan', 'laporan'); END IF; END $$
    """,
    """
    DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typnamespace = current_schema()::regnamespace AND typname = 'status_tugas') THEN CREATE TYPE status_tugas AS ENUM ('belum', 'selesai'); END IF; END $$
    """,
    """
    CREATE TABLE IF NOT EXISTS outlets (
        id VARCHAR NOT NULL,
        nama VARCHAR(120) NOT NULL,
        kode VARCHAR(16),
        nomor VARCHAR(8),
        aktif BOOLEAN DEFAULT true NOT NULL,
        lat FLOAT,
        lng FLOAT,
        radius_absen_m INTEGER,
        google_review_url VARCHAR(500),
        google_location_id VARCHAR(255),
        plot_modal_laci NUMERIC(12, 2),
        plot_uang_belanja NUMERIC(12, 2),
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_outlets PRIMARY KEY (id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS roles (
        id VARCHAR NOT NULL,
        nama VARCHAR(60) NOT NULL,
        keterangan VARCHAR(255),
        izin JSON NOT NULL,
        bawaan BOOLEAN NOT NULL,
        urutan INTEGER NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE,
        updated_at TIMESTAMP WITH TIME ZONE,
        CONSTRAINT pk_roles PRIMARY KEY (id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS staff (
        id VARCHAR NOT NULL,
        username VARCHAR(100) NOT NULL,
        name VARCHAR(255),
        password_hash VARCHAR(255) NOT NULL,
        no_hp VARCHAR(30),
        alamat VARCHAR(500),
        tanggal_lahir DATE,
        jenis_kelamin VARCHAR(10),
        email VARCHAR(255),
        kontak_darurat_nama VARCHAR(255),
        kontak_darurat_hp VARCHAR(30),
        kontak_darurat_hubungan VARCHAR(50),
        tanggal_bergabung DATE,
        foto_key VARCHAR(255),
        role_id VARCHAR NOT NULL,
        outlet_id VARCHAR,
        is_active BOOLEAN NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE,
        CONSTRAINT pk_staff PRIMARY KEY (id),
        CONSTRAINT fk_staff_role_id_roles FOREIGN KEY(role_id) REFERENCES roles (id) ON DELETE RESTRICT,
        CONSTRAINT fk_staff_outlet_id_outlets FOREIGN KEY(outlet_id) REFERENCES outlets (id) ON DELETE RESTRICT
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_staff_on_role_id ON staff (role_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_staff_on_outlet_id ON staff (outlet_id)
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS unique_staff_username ON staff (lower(username))
    """,
    """
    CREATE TABLE IF NOT EXISTS perangkat (
        id VARCHAR NOT NULL,
        outlet_id VARCHAR NOT NULL,
        nama VARCHAR(80) NOT NULL,
        bagian VARCHAR(30) NOT NULL,
        status VARCHAR(20) NOT NULL,
        kode_hash VARCHAR(64),
        kode_kedaluwarsa TIMESTAMP WITH TIME ZONE,
        token_hash VARCHAR(64),
        android_id VARCHAR(64),
        serial VARCHAR(80),
        merek VARCHAR(60),
        model VARCHAR(80),
        didaftarkan_oleh VARCHAR,
        dibuat_pada TIMESTAMP WITH TIME ZONE NOT NULL,
        dipasangkan_pada TIMESTAMP WITH TIME ZONE,
        terakhir_dipakai TIMESTAMP WITH TIME ZONE,
        CONSTRAINT pk_perangkat PRIMARY KEY (id),
        CONSTRAINT fk_perangkat_outlet_id_outlets FOREIGN KEY(outlet_id) REFERENCES outlets (id) ON DELETE RESTRICT,
        CONSTRAINT fk_perangkat_didaftarkan_oleh_staff FOREIGN KEY(didaftarkan_oleh) REFERENCES staff (id) ON DELETE SET NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_perangkat_on_outlet_id ON perangkat (outlet_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_perangkat_on_didaftarkan_oleh ON perangkat (didaftarkan_oleh)
    """,
    """
    CREATE TABLE IF NOT EXISTS perangkat_tautan (
        id VARCHAR NOT NULL,
        perangkat_id VARCHAR NOT NULL,
        token_hash VARCHAR(64) NOT NULL,
        kedaluwarsa TIMESTAMP WITH TIME ZONE NOT NULL,
        staff_id VARCHAR,
        ditautkan_pada TIMESTAMP WITH TIME ZONE,
        dibuat_pada TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_perangkat_tautan PRIMARY KEY (id),
        CONSTRAINT fk_perangkat_tautan_perangkat_id_perangkat FOREIGN KEY(perangkat_id) REFERENCES perangkat (id) ON DELETE CASCADE,
        CONSTRAINT fk_perangkat_tautan_staff_id_staff FOREIGN KEY(staff_id) REFERENCES staff (id) ON DELETE SET NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_perangkat_tautan_on_perangkat_id ON perangkat_tautan (perangkat_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_perangkat_tautan_on_staff_id ON perangkat_tautan (staff_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS stored_files (
        path VARCHAR(500) NOT NULL,
        content_type VARCHAR(100) NOT NULL,
        data BYTEA NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_stored_files PRIMARY KEY (path)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pengaturan_kafe (
        id VARCHAR NOT NULL,
        nama VARCHAR(120) NOT NULL,
        alamat TEXT NOT NULL,
        telepon VARCHAR(40) NOT NULL,
        nomor_aduan VARCHAR(40) NOT NULL,
        wifi JSON NOT NULL,
        wifi_password VARCHAR(120) NOT NULL,
        sosial JSON NOT NULL,
        ucapan_struk VARCHAR(200) NOT NULL,
        tahapan_pesanan JSON,
        toleransi_telat_menit INTEGER NOT NULL,
        potongan_telat_per_menit INTEGER NOT NULL,
        batas_tutup_otomatis_jam INTEGER NOT NULL,
        markup_hpp_persen NUMERIC(5, 2) NOT NULL,
        target_margin_persen NUMERIC(5, 2),
        tax_persen NUMERIC(5, 2) NOT NULL,
        service_persen NUMERIC(5, 2) NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_pengaturan_kafe PRIMARY KEY (id),
        CONSTRAINT fk_pengaturan_kafe_id_outlets FOREIGN KEY(id) REFERENCES outlets (id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS kategori_pengunjung (
        id VARCHAR NOT NULL,
        outlet_id VARCHAR NOT NULL,
        master_id VARCHAR,
        nama VARCHAR(40) NOT NULL,
        tanya_gender BOOLEAN NOT NULL,
        urutan INTEGER NOT NULL,
        aktif BOOLEAN NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_kategori_pengunjung PRIMARY KEY (id),
        CONSTRAINT fk_kategori_pengunjung_outlet_id_outlets FOREIGN KEY(outlet_id) REFERENCES outlets (id) ON DELETE CASCADE
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_kategori_pengunjung_on_outlet_id ON kategori_pengunjung (outlet_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS gender_pengunjung (
        id VARCHAR NOT NULL,
        outlet_id VARCHAR NOT NULL,
        nama VARCHAR(40) NOT NULL,
        urutan INTEGER NOT NULL,
        aktif BOOLEAN NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_gender_pengunjung PRIMARY KEY (id),
        CONSTRAINT fk_gender_pengunjung_outlet_id_outlets FOREIGN KEY(outlet_id) REFERENCES outlets (id) ON DELETE CASCADE
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_gender_pengunjung_on_outlet_id ON gender_pengunjung (outlet_id)
    """,
)


def upgrade() -> None:
    for statement in STATEMENTS:
        op.execute(statement)


def downgrade() -> None:
    # Irreversible by design (see the module docstring): no table is dropped.
    pass
