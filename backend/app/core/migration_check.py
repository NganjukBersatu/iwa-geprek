"""Migration checker (READ ONLY): snapshot before, compare after.

Used by scripts/pra_deploy.py. Every function takes a SQLAlchemy connection and never writes.

After a migration it checks that:
  * the row count of EVERY table that existed before is unchanged;
  * the sums of the key money and quantity columns are exactly the same.
"""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import Connection

# Tabel yang diisi migrasi dengan sengaja, beserta jumlah baris terbanyak yang boleh bertambah; berkurang tetap menghentikan deploy.
ROWS_ADDED_ON_PURPOSE = {"units": 8}

# Sums that must not change: (label, table, column), written with the names before the English-names migration; the new names are found through RENAMES.
SUMS = (
    ("orders.total", "orders", "total"),
    ("ingredient_cards.qty", "kartu_bahan", "qty"),
    ("stock_cards.qty", "kartu_stok", "qty"),
    ("expenses.amount", "expenses", "jumlah"),
)

RENAME_MIGRATIONS = tuple(Path(__file__).resolve().parents[2] / "alembic" / "versions" / name for name in ("j5o7g9i1c983_english_names.py", "k6p8h0j2d094_cash_sessions.py", "a1b3d5f7c905_staff_to_users.py"))


def _renames() -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    """The tables and columns the renaming migrations changed, read from those migrations so the lists are written once."""
    tables: dict[str, str] = {}
    columns: dict[str, dict[str, str]] = {}
    for source in RENAME_MIGRATIONS:
        spec = spec_from_file_location(source.stem, source)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load {source}")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        tables.update(module.TABLES)
        for table, pairs in getattr(module, "COLUMNS", {}).items():
            columns.setdefault(table, {}).update(pairs)
    return tables, columns


TABLE_RENAMES, COLUMN_RENAMES = _renames()


def _tables(conn: Connection) -> list[str]:
    rows = conn.execute(
        text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' "
            "AND table_name NOT IN ('alembic_version', 'alembic_version_v2') ORDER BY table_name"
        )
    )
    return [row[0] for row in rows]


def _has_column(conn: Connection, table: str, column: str) -> bool:
    return bool(
        conn.scalar(
            text(
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = :t AND column_name = :k"
            ),
            {"t": table, "k": column},
        )
    )


def _locate(conn: Connection, table: str, column: str) -> tuple[str, str] | None:
    """Where a column lives now: under its old name before the English-names migration, under the new one after it."""
    renamed = (TABLE_RENAMES.get(table, table), COLUMN_RENAMES.get(table, {}).get(column, column))
    for candidate in ((table, column), renamed):
        if _has_column(conn, *candidate):
            return candidate
    return None


def snapshot(conn: Connection) -> dict:
    result: dict = {"rows": {}, "sums": {}}
    for table in _tables(conn):
        result["rows"][table] = conn.scalar(text(f'SELECT count(*) FROM "{table}"'))
    for label, table, column in SUMS:
        found = _locate(conn, table, column)
        if found:
            result["sums"][label] = str(conn.scalar(text(f'SELECT coalesce(sum("{found[1]}"), 0) FROM "{found[0]}"')))
    return result


def check(conn: Connection, before: dict) -> tuple[list[str], list[str]]:
    """Compare the current state with `before` (a snapshot()); returns (problems, notes), a non-empty `problems` means stop."""
    after = snapshot(conn)
    problems: list[str] = []
    notes: list[str] = []

    for table, count in before["rows"].items():
        now = after["rows"].get(table)
        if now is None and table in TABLE_RENAMES:
            now = after["rows"].get(TABLE_RENAMES[table])
        if now is None:
            problems.append(f"table {table} disappeared")
        elif table in ROWS_ADDED_ON_PURPOSE and count <= now <= count + ROWS_ADDED_ON_PURPOSE[table]:
            if now != count:
                notes.append(f"table {table} gained {now - count} rows on purpose")
        elif now != count:
            problems.append(f"{table}: row count changed ({count} -> {now})")

    for label, value in before["sums"].items():
        if after["sums"].get(label) != value:
            problems.append(f"{label}: changed ({value} -> {after['sums'].get(label)})")

    created = sorted(set(after["rows"]) - set(before["rows"]) - set(TABLE_RENAMES.values()))
    if created:
        notes.append(f"new tables: {', '.join(created)}")
    return problems, notes
