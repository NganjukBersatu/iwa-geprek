"""Snapshot data demo: isi satu skema disimpan sekali sebagai JSON terkompresi, lalu dimuat ulang dengan tanggal digeser ke hari ini.

Berkasnya milik klien (backend/demo/snapshot.json.gz) dan ikut deploy; tidak ada database tambahan. Nilai disimpan bertipe supaya
waktu, tanggal, uang, dan berkas biner kembali persis. Saat dimuat, pemicu tabel dimatikan sementara karena nilai turunannya (hari
bisnis, saldo stok, jejak uang) sudah ikut tersimpan.
"""
import base64
import gzip
import json
from collections.abc import Callable, Iterator
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import Connection

from app.core.clock import WIB, now

FORMAT = 1
SNAPSHOT_PATH = Path(__file__).resolve().parents[3] / "demo" / "snapshot.json.gz"
# Tabel milik mekanisme migrasi dan status demo tidak ikut disimpan atau dimuat.
SKIPPED_TABLES = frozenset({"alembic_version", "alembic_version_v2", "demo_state"})
BATCH_ROWS = 1000
TIMESTAMP_TYPES = frozenset({"timestamp with time zone", "timestamp without time zone"})
DATE_TYPE = "date"
TIME_TYPES = frozenset({"time without time zone", "time with time zone"})
NUMERIC_TYPE = "numeric"
BYTES_TYPE = "bytea"
UUID_TYPE = "uuid"
JSON_TYPES = frozenset({"json", "jsonb"})


class SnapshotError(Exception):
    """Snapshot tidak ada, rusak, atau tidak cocok dengan tabel; pesannya untuk developer."""


def _columns(conn: Connection, schema: str, table: str) -> list[tuple[str, str]]:
    rows = conn.execute(
        text("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = :schema AND table_name = :table ORDER BY ordinal_position"),
        {"schema": schema, "table": table},
    )
    return [(row.column_name, row.data_type) for row in rows]


def _tables(conn: Connection, schema: str) -> list[str]:
    names = conn.scalars(text("SELECT tablename FROM pg_tables WHERE schemaname = :schema ORDER BY tablename"), {"schema": schema})
    return [name for name in names if name not in SKIPPED_TABLES]


def _plan(conn: Connection, schema: str, tables: list[str]) -> tuple[list[str], dict[str, set[str]]]:
    """Urutan muat dan kolom yang diisi belakangan.

    Tabel diurutkan menurut kunci asing wajib saja. Kunci asing yang boleh kosong tetapi menunjuk ke tabel yang dimuat sesudahnya
    (termasuk tabel itu sendiri) dimuat kosong dulu lalu diisi setelah semua tabel masuk, supaya hubungan berputar tetap bisa dimuat.
    """
    edges = conn.execute(
        text(
            "SELECT c.conrelid::regclass::text AS child, c.confrelid::regclass::text AS parent, "
            "array_agg(a.attname::text) AS columns, bool_and(a.attnotnull) AS required "
            "FROM pg_constraint c JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY (c.conkey) "
            "WHERE c.contype = 'f' AND c.connamespace = to_regnamespace(:schema) GROUP BY c.oid, c.conrelid, c.confrelid"
        ),
        {"schema": schema},
    ).all()
    bare = {f"{schema}.{name}": name for name in tables} | {name: name for name in tables}
    known = [(bare.get(edge.child), bare.get(edge.parent), list(edge.columns), edge.required) for edge in edges]
    known = [(child, parent, columns, required) for child, parent, columns, required in known if child is not None and parent is not None]
    parents: dict[str, set[str]] = {name: set() for name in tables}
    for child, parent, _, required in known:
        if required and child != parent:
            parents[child].add(parent)
    ordered: list[str] = []
    placed: set[str] = set()
    remaining = sorted(tables)
    while remaining:
        ready = [name for name in remaining if parents[name] <= placed]
        if not ready:
            raise SnapshotError(f"Kunci asing wajib berputar di antara: {', '.join(remaining)}")
        ordered.extend(ready)
        placed.update(ready)
        remaining = [name for name in remaining if name not in placed]
    position = {name: index for index, name in enumerate(ordered)}
    deferred: dict[str, set[str]] = {}
    for child, parent, columns, required in known:
        if not required and position[parent] >= position[child]:
            deferred.setdefault(child, set()).update(columns)
    return ordered, deferred


def _primary_key(conn: Connection, schema: str, table: str) -> list[str]:
    return list(
        conn.scalars(
            text(
                "SELECT a.attname FROM pg_index i JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY (i.indkey) "
                "WHERE i.indrelid = to_regclass(:table) AND i.indisprimary ORDER BY array_position(i.indkey, a.attnum)"
            ),
            {"table": f"{schema}.{table}"},
        )
    )


def _plain(value: object, kind: str) -> object:
    if value is None:
        return None
    if kind in TIMESTAMP_TYPES or kind == DATE_TYPE or kind in TIME_TYPES:
        return value.isoformat()
    if kind == NUMERIC_TYPE:
        return str(value)
    if kind == BYTES_TYPE:
        return base64.b64encode(bytes(value)).decode("ascii")
    if kind == UUID_TYPE:
        return str(value)
    return value


def export(conn: Connection, schema: str, revision: str, path: Path = SNAPSHOT_PATH) -> dict[str, int]:
    """Menulis seluruh isi skema ke berkas snapshot; mengembalikan jumlah baris per tabel."""
    tables, _ = _plan(conn, schema, _tables(conn, schema))
    body: list[dict] = []
    counts: dict[str, int] = {}
    for table in tables:
        columns = _columns(conn, schema, table)
        names = ", ".join(f'"{name}"' for name, _ in columns)
        rows = [[_plain(value, kind) for value, (_, kind) in zip(row, columns, strict=True)] for row in conn.execute(text(f'SELECT {names} FROM "{schema}"."{table}"'))]
        body.append({"name": table, "columns": [{"name": name, "type": kind} for name, kind in columns], "rows": rows})
        counts[table] = len(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    document = {"format": FORMAT, "created_at": now().isoformat(), "revision": revision, "tables": body}
    with gzip.open(path, "wt", encoding="utf-8", compresslevel=9) as out:
        json.dump(document, out, ensure_ascii=False, separators=(",", ":"))
    return counts


def read(path: Path = SNAPSHOT_PATH) -> dict:
    if not path.is_file():
        raise SnapshotError(f"{path} tidak ada")
    try:
        with gzip.open(path, "rt", encoding="utf-8") as source:
            document = json.load(source)
    except (OSError, json.JSONDecodeError) as error:
        raise SnapshotError(f"{path} tidak bisa dibaca") from error
    if not isinstance(document, dict) or document.get("format") != FORMAT or not isinstance(document.get("tables"), list):
        raise SnapshotError(f"{path} bukan snapshot demo format {FORMAT}")
    return document


def day_shift(created_at: datetime, moment: datetime) -> int:
    """Hari yang ditambahkan ke setiap tanggal; jam tetap sama, dan bila jam pembuatan belum terlewati hari ini, mundur sehari supaya tidak ada data di masa depan."""
    created = created_at.astimezone(WIB)
    current = moment.astimezone(WIB)
    days = (current.date() - created.date()).days
    return days - 1 if created.timetz() > current.timetz() else days


def _restore(value: object, kind: str, days: int) -> object:
    if value is None:
        return None
    if kind in TIMESTAMP_TYPES:
        return datetime.fromisoformat(value) + timedelta(days=days)
    if kind == DATE_TYPE:
        return date.fromisoformat(value) + timedelta(days=days)
    if kind in TIME_TYPES:
        return time.fromisoformat(value)
    if kind == NUMERIC_TYPE:
        return Decimal(value)
    if kind == BYTES_TYPE:
        return base64.b64decode(value)
    if kind in JSON_TYPES:
        return json.dumps(value)
    return value


def _batches(rows: list[list], size: int) -> Iterator[list[list]]:
    for start in range(0, len(rows), size):
        yield rows[start : start + size]


def load(conn: Connection, schema: str, document: dict, progress: Callable[[int], None]) -> None:
    """Memuat snapshot ke skema yang tabelnya sudah dibuat migrasi; kolom baru di kode memakai nilai bawaannya, kolom yang sudah hilang diabaikan."""
    days = day_shift(datetime.fromisoformat(document["created_at"]), now())
    present = set(_tables(conn, schema))
    by_name = {table["name"]: table for table in document["tables"] if table.get("name") in present}
    order, deferred = _plan(conn, schema, sorted(present))
    # Migrasi sudah mengisi beberapa baris awal (misalnya satuan); snapshot memuat isi lengkap skema yang dibangun migrasi yang sama, jadi baris awal itu dibuang dulu.
    if present:
        conn.execute(text("TRUNCATE " + ", ".join(f'"{schema}"."{name}"' for name in sorted(present)) + " RESTART IDENTITY CASCADE"))
    ordered = [name for name in order if name in by_name]
    total = sum(len(by_name[name]["rows"]) for name in ordered) or 1
    done = 0
    later: list[tuple[str, list[str], list[str], list[dict]]] = []
    for name in ordered:
        table = by_name[name]
        current = {column for column, _ in _columns(conn, schema, name)}
        kept = [(index, column["name"], column["type"]) for index, column in enumerate(table["columns"]) if column["name"] in current]
        if not kept or not table["rows"]:
            continue
        target = f'"{schema}"."{name}"'
        postponed = deferred.get(name, set())
        names = ", ".join(f'"{column}"' for _, column, _ in kept)
        placeholders = ", ".join(f"CAST(:c{position} AS {kind})" if kind in JSON_TYPES else f":c{position}" for position, (_, _, kind) in enumerate(kept))
        statement = text(f"INSERT INTO {target} ({names}) VALUES ({placeholders})")
        conn.execute(text(f"ALTER TABLE {target} DISABLE TRIGGER USER"))
        for batch in _batches(table["rows"], BATCH_ROWS):
            values = [{f"c{position}": _restore(row[index], kind, days) for position, (index, _, kind) in enumerate(kept)} for row in batch]
            filled = [dict(value) for value in values]
            for value in values:
                for position, (_, column, _) in enumerate(kept):
                    if column in postponed:
                        value[f"c{position}"] = None
            conn.execute(statement, values)
            if postponed:
                later.append((name, _primary_key(conn, schema, name), sorted(postponed & {column for _, column, _ in kept}), _named(kept, filled)))
            done += len(batch)
            progress(min(99, done * 100 // total))
        conn.execute(text(f"ALTER TABLE {target} ENABLE TRIGGER USER"))
    for name, key, columns, rows in later:
        _fill_later(conn, schema, name, key, columns, rows)
    _reset_sequences(conn, schema)


def _named(kept: list[tuple[int, str, str]], values: list[dict]) -> list[dict]:
    return [{column: value[f"c{position}"] for position, (_, column, _) in enumerate(kept)} for value in values]


def _fill_later(conn: Connection, schema: str, table: str, key: list[str], columns: list[str], rows: list[dict]) -> None:
    """Mengisi kunci asing yang dimuat kosong, setelah baris induknya sudah ada."""
    if not key or not columns:
        return
    wanted = [row for row in rows if any(row.get(column) is not None for column in columns)]
    if not wanted:
        return
    assignments = ", ".join(f'"{column}" = :{column}' for column in columns)
    match = " AND ".join(f'"{column}" = :{column}' for column in key)
    statement = text(f'UPDATE "{schema}"."{table}" SET {assignments} WHERE {match}')
    target = f'"{schema}"."{table}"'
    conn.execute(text(f"ALTER TABLE {target} DISABLE TRIGGER USER"))
    for batch in _batches(wanted, BATCH_ROWS):
        conn.execute(statement, [{column: row.get(column) for column in {*columns, *key}} for row in batch])
    conn.execute(text(f"ALTER TABLE {target} ENABLE TRIGGER USER"))


def _reset_sequences(conn: Connection, schema: str) -> None:
    """Nomor urut otomatis melanjutkan dari nilai terbesar yang dimuat, supaya baris baru selama demo tidak bentrok."""
    owned = conn.execute(
        text(
            "SELECT t.relname AS table_name, a.attname AS column_name, s.oid::regclass::text AS sequence FROM pg_class s "
            "JOIN pg_depend d ON d.objid = s.oid AND d.deptype IN ('a', 'i') JOIN pg_class t ON t.oid = d.refobjid "
            "JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = d.refobjsubid "
            "WHERE s.relkind = 'S' AND s.relnamespace = to_regnamespace(:schema)"
        ),
        {"schema": schema},
    ).all()
    for row in owned:
        conn.execute(
            text(f'SELECT setval(:sequence, COALESCE((SELECT max("{row.column_name}") FROM "{schema}"."{row.table_name}"), 0) + 1, false)'),
            {"sequence": row.sequence},
        )
