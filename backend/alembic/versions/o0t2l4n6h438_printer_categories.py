"""menu categories per branch printer, the printers each tablet reports, and the print mode of a branch

Revision ID: o0t2l4n6h438
Revises: n9s1k3m5g327
Create Date: 2026-11-10 12:00:00.000000

The list of categories belongs to the branch, not to a tablet or a printer, so it survives a tablet being removed or a printer being replaced; a tablet's report
belongs to the tablet. The list is filled once from `categories.station` for every branch, without touching that column and without overwriting a row that is
already there. `outlets.print_mode` starts as 'cashier', the behavior before this release. Every step looks first, so a second run changes nothing; foreign keys
are added without validation and validated in a step of their own. Down drops the tables and the column.
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'o0t2l4n6h438'
down_revision: Union[str, Sequence[str], None] = 'n9s1k3m5g327'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIMEOUTS = ("SET LOCAL lock_timeout = '1s'", "SET LOCAL statement_timeout = '180s'")

TABLES = (
    """
    CREATE TABLE IF NOT EXISTS printer_categories (
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        outlet_id TEXT NOT NULL,
        category_id TEXT NOT NULL,
        printer_slot TEXT NOT NULL,
        created_by TEXT,
        CONSTRAINT pk_printer_categories PRIMARY KEY (outlet_id, category_id),
        CONSTRAINT check_printer_categories_printer_slot_enum CHECK (printer_slot IN ('bar', 'kitchen'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS device_printers (
        reported_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        device_id TEXT NOT NULL,
        printer_slot TEXT NOT NULL,
        printer_name TEXT NOT NULL,
        printer_address TEXT NOT NULL,
        connection TEXT NOT NULL,
        CONSTRAINT pk_device_printers PRIMARY KEY (device_id, printer_slot),
        CONSTRAINT check_device_printers_printer_slot_enum CHECK (printer_slot IN ('receipt', 'bar', 'kitchen', 'station')),
        CONSTRAINT check_device_printers_connection_enum CHECK (connection IN ('connected', 'disconnected')),
        CONSTRAINT check_device_printers_printer_name_length CHECK (char_length(printer_name) BETWEEN 1 AND 120),
        CONSTRAINT check_device_printers_printer_address_length CHECK (char_length(printer_address) BETWEEN 1 AND 64)
    )
    """,
)

INDEXES = (
    'CREATE INDEX IF NOT EXISTS index_printer_categories_on_category_id ON printer_categories (category_id)',
    'CREATE INDEX IF NOT EXISTS index_printer_categories_on_created_by ON printer_categories (created_by)',
)

# (table, name, column, target, action); the list is part of the branch's settings, the report part of its tablet.
FOREIGN_KEYS = (
    ('printer_categories', 'fk_printer_categories_outlet_id_outlets', 'outlet_id', 'outlets', 'CASCADE'),
    ('printer_categories', 'fk_printer_categories_category_id_categories', 'category_id', 'categories', 'CASCADE'),
    ('printer_categories', 'fk_printer_categories_created_by_staff', 'created_by', 'staff', 'SET NULL'),
    ('device_printers', 'fk_device_printers_device_id_devices', 'device_id', 'devices', 'CASCADE'),
)

BACKFILL = """
INSERT INTO printer_categories (outlet_id, category_id, printer_slot)
SELECT o.id, c.id, CASE c.station WHEN 'bar' THEN 'bar' ELSE 'kitchen' END
FROM outlets o
CROSS JOIN categories c
WHERE c.kind = 'menu' AND c.station IN ('bar', 'dapur')
ON CONFLICT (outlet_id, category_id) DO NOTHING
"""

PRINT_MODE = (
    "ALTER TABLE outlets ADD COLUMN IF NOT EXISTS print_mode TEXT NOT NULL DEFAULT 'cashier'",
    """
    DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'check_outlets_print_mode_enum') THEN
            ALTER TABLE outlets ADD CONSTRAINT check_outlets_print_mode_enum CHECK (print_mode IN ('cashier', 'station')) NOT VALID;
        END IF;
    END $$;
    """,
    'ALTER TABLE outlets VALIDATE CONSTRAINT check_outlets_print_mode_enum',
)

DROP_PRINT_MODE = (
    'ALTER TABLE outlets DROP CONSTRAINT IF EXISTS check_outlets_print_mode_enum',
    'ALTER TABLE outlets DROP COLUMN IF EXISTS print_mode',
)


def _foreign_key(table: str, name: str, column: str, target: str, action: str) -> str:
    return f"""
    DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '{name}') THEN
            ALTER TABLE {table} ADD CONSTRAINT {name} FOREIGN KEY ({column}) REFERENCES {target}(id) ON DELETE {action} NOT VALID;
        END IF;
    END $$;
    """


def upgrade() -> None:
    for statement in TIMEOUTS:
        op.execute(statement)
    for statement in TABLES:
        op.execute(statement)
    for statement in INDEXES:
        op.execute(statement)
    for table, name, column, target, action in FOREIGN_KEYS:
        op.execute(_foreign_key(table, name, column, target, action))
    for table, name, _column, _target, _action in FOREIGN_KEYS:
        op.execute(f'ALTER TABLE {table} VALIDATE CONSTRAINT {name}')
    op.execute(BACKFILL)
    for statement in PRINT_MODE:
        op.execute(statement)


def downgrade() -> None:
    for statement in DROP_PRINT_MODE:
        op.execute(statement)
    op.execute('DROP TABLE IF EXISTS device_printers')
    op.execute('DROP TABLE IF EXISTS printer_categories')
