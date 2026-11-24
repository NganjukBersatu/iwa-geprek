"""Tabel kejadian absen: kunci idempotensi dan jejak waktu absen offline; Down tanpa aksi karena menghapus tabel membuang jejak audit.

Revision ID: v7b9s1u3o105
Revises: u6z8r0t2n094
Create Date: 2026-11-13 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'v7b9s1u3o105'
down_revision: Union[str, Sequence[str], None] = 'u6z8r0t2n094'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")

TABLE = """
CREATE TABLE IF NOT EXISTS attendance_clock_events (
    captured_at timestamptz NOT NULL,
    submitted_at timestamptz NOT NULL,
    needs_review boolean NOT NULL DEFAULT false,
    id text NOT NULL,
    staff_id text NOT NULL,
    attendance_id text NOT NULL,
    idempotency_key text NOT NULL,
    kind text NOT NULL,
    time_source text NOT NULL,
    request_hash text NOT NULL,
    CONSTRAINT pk_attendance_clock_events PRIMARY KEY (id),
    CONSTRAINT check_attendance_clock_events_id_length CHECK (char_length(id) BETWEEN 1 AND 64),
    CONSTRAINT check_attendance_clock_events_idempotency_key_length CHECK (char_length(idempotency_key) BETWEEN 8 AND 64),
    CONSTRAINT check_attendance_clock_events_kind_values CHECK (kind IN ('clock_in', 'clock_out')),
    CONSTRAINT check_attendance_clock_events_time_source_values CHECK (time_source IN ('server_anchored', 'device_clock')),
    CONSTRAINT check_attendance_clock_events_request_hash_length CHECK (char_length(request_hash) = 64)
)
"""

INDEXES = (
    'CREATE UNIQUE INDEX IF NOT EXISTS unique_attendance_clock_events_staff_id_idempotency_key ON attendance_clock_events (staff_id, idempotency_key)',
    'CREATE INDEX IF NOT EXISTS index_attendance_clock_events_on_attendance_id ON attendance_clock_events (attendance_id)',
)

FOREIGN_KEYS = (
    """
    DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE connamespace = current_schema()::regnamespace AND conname = 'fk_attendance_clock_events_staff_id_staff') THEN
            ALTER TABLE attendance_clock_events ADD CONSTRAINT fk_attendance_clock_events_staff_id_staff FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE RESTRICT NOT VALID;
        END IF;
    END $$;
    """,
    'ALTER TABLE attendance_clock_events VALIDATE CONSTRAINT fk_attendance_clock_events_staff_id_staff',
    """
    DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE connamespace = current_schema()::regnamespace AND conname = 'fk_attendance_clock_events_attendance_id_attendance_records') THEN
            ALTER TABLE attendance_clock_events ADD CONSTRAINT fk_attendance_clock_events_attendance_id_attendance_records FOREIGN KEY (attendance_id) REFERENCES attendance_records(id) ON DELETE RESTRICT NOT VALID;
        END IF;
    END $$;
    """,
    'ALTER TABLE attendance_clock_events VALIDATE CONSTRAINT fk_attendance_clock_events_attendance_id_attendance_records',
)


def upgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    op.execute(TABLE)
    for statement in INDEXES:
        op.execute(statement)
    for statement in FOREIGN_KEYS:
        op.execute(statement)


def downgrade() -> None:
    pass
