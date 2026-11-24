"""base schema: schedules, attendance, overtime, leave requests, procedures and personal tasks

Revision ID: a0b1c2d3e404
Revises: a0b1c2d3e403

The v2 chain started on top of tables owned by a legacy chain that is not in this repository, so a database built from nothing
could not be created. This revision and its three siblings create those tables, in the shape the chain expects to find them:
columns that later revisions add (roles.is_admin, expenses.bahan_id, the business_day columns, ...) are left out on purpose.

Every statement is IF NOT EXISTS, so a database that already has the tables (production, staging) is left exactly as it is.
Down is a no-op: dropping the core tables would destroy data, and a mistake after release is fixed with a forward migration.
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'a0b1c2d3e404'
down_revision: Union[str, Sequence[str], None] = 'a0b1c2d3e403'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS jadwal_shift (
        id VARCHAR NOT NULL,
        outlet_id VARCHAR NOT NULL,
        tanggal DATE NOT NULL,
        kasir_id VARCHAR NOT NULL,
        kode_shift_id VARCHAR,
        starts_at TIMESTAMP WITH TIME ZONE,
        ends_at TIMESTAMP WITH TIME ZONE,
        role_id VARCHAR,
        catatan VARCHAR,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_jadwal_shift PRIMARY KEY (id),
        CONSTRAINT fk_jadwal_shift_outlet_id_outlets FOREIGN KEY(outlet_id) REFERENCES outlets (id) ON DELETE RESTRICT,
        CONSTRAINT fk_jadwal_shift_kasir_id_staff FOREIGN KEY(kasir_id) REFERENCES staff (id) ON DELETE RESTRICT,
        CONSTRAINT fk_jadwal_shift_kode_shift_id_kode_shift FOREIGN KEY(kode_shift_id) REFERENCES kode_shift (id) ON DELETE SET NULL,
        CONSTRAINT fk_jadwal_shift_role_id_roles FOREIGN KEY(role_id) REFERENCES roles (id) ON DELETE SET NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_jadwal_shift_on_kode_shift_id ON jadwal_shift (kode_shift_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_jadwal_shift_on_role_id ON jadwal_shift (role_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS jadwal_libur (
        id VARCHAR NOT NULL,
        outlet_id VARCHAR NOT NULL,
        tanggal DATE NOT NULL,
        staff_id VARCHAR NOT NULL,
        kode_shift_id VARCHAR,
        catatan VARCHAR,
        CONSTRAINT pk_jadwal_libur PRIMARY KEY (id),
        CONSTRAINT fk_jadwal_libur_outlet_id_outlets FOREIGN KEY(outlet_id) REFERENCES outlets (id) ON DELETE RESTRICT,
        CONSTRAINT fk_jadwal_libur_staff_id_staff FOREIGN KEY(staff_id) REFERENCES staff (id) ON DELETE RESTRICT,
        CONSTRAINT fk_jadwal_libur_kode_shift_id_kode_shift FOREIGN KEY(kode_shift_id) REFERENCES kode_shift (id) ON DELETE SET NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_jadwal_libur_on_staff_id ON jadwal_libur (staff_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_jadwal_libur_on_kode_shift_id ON jadwal_libur (kode_shift_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS absensi (
        id VARCHAR NOT NULL,
        outlet_id VARCHAR NOT NULL,
        staff_id VARCHAR NOT NULL,
        tanggal DATE NOT NULL,
        kode_shift_id VARCHAR,
        jadwal_id VARCHAR,
        status status_kehadiran NOT NULL,
        jam_masuk TIMESTAMP WITH TIME ZONE,
        jam_keluar TIMESTAMP WITH TIME ZONE,
        ditutup_otomatis BOOLEAN DEFAULT false NOT NULL,
        tutup_otomatis_dilihat BOOLEAN DEFAULT false NOT NULL,
        catatan VARCHAR,
        alasan_di_luar_jadwal VARCHAR,
        foto_path VARCHAR,
        lat_masuk FLOAT,
        lng_masuk FLOAT,
        akurasi_masuk FLOAT,
        mode_masuk VARCHAR(10),
        catatan_lokasi_masuk VARCHAR,
        jarak_masuk FLOAT,
        radius_masuk INTEGER,
        foto_pulang_path VARCHAR,
        lat_pulang FLOAT,
        lng_pulang FLOAT,
        akurasi_pulang FLOAT,
        mode_pulang VARCHAR(10),
        catatan_lokasi_pulang VARCHAR,
        jarak_pulang FLOAT,
        radius_pulang INTEGER,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_absensi PRIMARY KEY (id),
        CONSTRAINT fk_absensi_outlet_id_outlets FOREIGN KEY(outlet_id) REFERENCES outlets (id) ON DELETE RESTRICT,
        CONSTRAINT fk_absensi_staff_id_staff FOREIGN KEY(staff_id) REFERENCES staff (id) ON DELETE RESTRICT,
        CONSTRAINT fk_absensi_kode_shift_id_kode_shift FOREIGN KEY(kode_shift_id) REFERENCES kode_shift (id) ON DELETE SET NULL,
        CONSTRAINT fk_absensi_jadwal_id_jadwal_shift FOREIGN KEY(jadwal_id) REFERENCES jadwal_shift (id) ON DELETE SET NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_absensi_on_kode_shift_id ON absensi (kode_shift_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_absensi_on_jadwal_id ON absensi (jadwal_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS lembur (
        id VARCHAR NOT NULL,
        outlet_id VARCHAR NOT NULL,
        staff_id VARCHAR NOT NULL,
        tanggal DATE NOT NULL,
        mulai TIMESTAMP WITH TIME ZONE NOT NULL,
        selesai TIMESTAMP WITH TIME ZONE,
        catatan VARCHAR,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_lembur PRIMARY KEY (id),
        CONSTRAINT fk_lembur_outlet_id_outlets FOREIGN KEY(outlet_id) REFERENCES outlets (id) ON DELETE RESTRICT,
        CONSTRAINT fk_lembur_staff_id_staff FOREIGN KEY(staff_id) REFERENCES staff (id) ON DELETE RESTRICT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pengajuan_izin (
        id VARCHAR NOT NULL,
        outlet_id VARCHAR,
        staff_id VARCHAR NOT NULL,
        jenis jenis_pengajuan NOT NULL,
        tanggal_mulai DATE NOT NULL,
        tanggal_selesai DATE NOT NULL,
        alasan VARCHAR NOT NULL,
        status status_pengajuan NOT NULL,
        diputus_oleh_id VARCHAR,
        diputus_pada TIMESTAMP WITH TIME ZONE,
        catatan_atasan VARCHAR,
        lampiran_path VARCHAR,
        lampiran_link VARCHAR(2000),
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_pengajuan_izin PRIMARY KEY (id),
        CONSTRAINT fk_pengajuan_izin_outlet_id_outlets FOREIGN KEY(outlet_id) REFERENCES outlets (id) ON DELETE SET NULL,
        CONSTRAINT fk_pengajuan_izin_staff_id_staff FOREIGN KEY(staff_id) REFERENCES staff (id) ON DELETE RESTRICT,
        CONSTRAINT fk_pengajuan_izin_diputus_oleh_id_staff FOREIGN KEY(diputus_oleh_id) REFERENCES staff (id) ON DELETE SET NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_pengajuan_izin_on_outlet_id ON pengajuan_izin (outlet_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_pengajuan_izin_on_staff_id ON pengajuan_izin (staff_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_pengajuan_izin_on_diputus_oleh_id ON pengajuan_izin (diputus_oleh_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS sop (
        id VARCHAR NOT NULL,
        judul VARCHAR(120) NOT NULL,
        aktif BOOLEAN NOT NULL,
        urutan INTEGER NOT NULL,
        versi INTEGER NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_sop PRIMARY KEY (id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS sop_slide (
        id VARCHAR NOT NULL,
        sop_id VARCHAR NOT NULL,
        urutan INTEGER NOT NULL,
        judul VARCHAR(120) NOT NULL,
        isi VARCHAR NOT NULL,
        CONSTRAINT pk_sop_slide PRIMARY KEY (id),
        CONSTRAINT fk_sop_slide_sop_id_sop FOREIGN KEY(sop_id) REFERENCES sop (id) ON DELETE CASCADE
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_sop_slide_on_sop_id ON sop_slide (sop_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS tugas (
        id VARCHAR NOT NULL,
        outlet_id VARCHAR,
        jenis jenis_tugas NOT NULL,
        status status_tugas NOT NULL,
        judul VARCHAR(200) NOT NULL,
        keterangan VARCHAR,
        ditugaskan_ke_id VARCHAR NOT NULL,
        dibuat_oleh_id VARCHAR,
        foto_tugas_path VARCHAR,
        tenggat TIMESTAMP WITH TIME ZONE,
        catatan_selesai VARCHAR,
        foto_selesai_path VARCHAR,
        selesai_pada TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_tugas PRIMARY KEY (id),
        CONSTRAINT fk_tugas_outlet_id_outlets FOREIGN KEY(outlet_id) REFERENCES outlets (id) ON DELETE RESTRICT,
        CONSTRAINT fk_tugas_ditugaskan_ke_id_staff FOREIGN KEY(ditugaskan_ke_id) REFERENCES staff (id) ON DELETE RESTRICT,
        CONSTRAINT fk_tugas_dibuat_oleh_id_staff FOREIGN KEY(dibuat_oleh_id) REFERENCES staff (id) ON DELETE SET NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_tugas_on_outlet_id ON tugas (outlet_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_tugas_on_ditugaskan_ke_id ON tugas (ditugaskan_ke_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_tugas_on_dibuat_oleh_id ON tugas (dibuat_oleh_id)
    """,
)


def upgrade() -> None:
    for statement in STATEMENTS:
        op.execute(statement)


def downgrade() -> None:
    # Irreversible by design (see the module docstring): no table is dropped.
    pass
