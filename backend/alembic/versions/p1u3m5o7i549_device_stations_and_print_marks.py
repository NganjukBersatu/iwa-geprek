"""stations held by each tablet, the mark of a printed station ticket, and the index of the open station queue

Revision ID: p1u3m5o7i549
Revises: o0t2l4n6h438
Create Date: 2026-11-10 14:00:00.000000

A tablet shows one tab for every station it holds, and the tablet holding the cashier station is the one that may open a till session. A tablet already running
keeps working: it holds the station of the role of the account that last signed in on it, and a tablet of the old cashier section holds the cashier station. Rows
that are already there are not overwritten. `station_tasks.printed_at` is set by the first tablet to claim a ticket, so a second tablet at the same station does
not print it again. The partial index serves the queue, which follows the state of the dish and not the cash session; it covers only tasks still alive.
Every step looks first, so a second run changes nothing. The `hold_for_food` columns stay until the code no longer reads them. Down drops what this adds.
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'p1u3m5o7i549'
down_revision: Union[str, Sequence[str], None] = 'o0t2l4n6h438'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")

TABLE = """
CREATE TABLE IF NOT EXISTS device_stations (
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    device_id TEXT NOT NULL,
    station_id TEXT NOT NULL,
    CONSTRAINT pk_device_stations PRIMARY KEY (device_id, station_id)
)
"""

INDEXES = (
    'CREATE INDEX IF NOT EXISTS index_device_stations_on_station_id ON device_stations (station_id)',
    'CREATE INDEX IF NOT EXISTS index_station_tasks_on_outlet_id_open ON station_tasks (outlet_id, order_id) WHERE finished_at IS NULL AND acknowledged_at IS NULL',
)

# A station is part of the tablet that holds it, and goes with it or with the station.
FOREIGN_KEYS = (
    ('device_stations', 'fk_device_stations_device_id_devices', 'device_id', 'devices', 'CASCADE'),
    ('device_stations', 'fk_device_stations_station_id_stations', 'station_id', 'stations', 'CASCADE'),
)

COLUMNS = ('ALTER TABLE station_tasks ADD COLUMN IF NOT EXISTS printed_at TIMESTAMPTZ',)

BACKFILL = (
    """
    INSERT INTO device_stations (device_id, station_id)
    SELECT DISTINCT ON (l.device_id) l.device_id, r.station_id
    FROM device_links l
    JOIN devices d ON d.id = l.device_id AND d.status = 'terdaftar'
    JOIN staff s ON s.id = l.staff_id
    JOIN roles r ON r.id = s.role_id
    JOIN stations st ON st.id = r.station_id
    WHERE l.linked_at IS NOT NULL
    ORDER BY l.device_id, l.linked_at DESC
    ON CONFLICT (device_id, station_id) DO NOTHING
    """,
    """
    INSERT INTO device_stations (device_id, station_id)
    SELECT d.id, st.id
    FROM devices d
    JOIN stations st ON st.kind = 'handover'
    WHERE d.status = 'terdaftar' AND d.section = 'kasir'
    ON CONFLICT (device_id, station_id) DO NOTHING
    """,
)

DROP = (
    'DROP INDEX IF EXISTS index_station_tasks_on_outlet_id_open',
    'ALTER TABLE station_tasks DROP COLUMN IF EXISTS printed_at',
    'DROP TABLE IF EXISTS device_stations',
)


def _foreign_key(table: str, name: str, column: str, target: str, action: str) -> str:
    return f"""
    DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE connamespace = current_schema()::regnamespace AND conname = '{name}') THEN
            ALTER TABLE {table} ADD CONSTRAINT {name} FOREIGN KEY ({column}) REFERENCES {target}(id) ON DELETE {action} NOT VALID;
        END IF;
    END $$;
    """


def upgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    op.execute(TABLE)
    for statement in COLUMNS:
        op.execute(statement)
    for statement in INDEXES:
        op.execute(statement)
    for table, name, column, target, action in FOREIGN_KEYS:
        op.execute(_foreign_key(table, name, column, target, action))
    for table, name, _column, _target, _action in FOREIGN_KEYS:
        op.execute(f'ALTER TABLE {table} VALIDATE CONSTRAINT {name}')
    for statement in BACKFILL:
        op.execute(statement)


def downgrade() -> None:
    for statement in DROP:
        op.execute(statement)
