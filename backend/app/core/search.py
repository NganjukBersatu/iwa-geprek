"""The one way to search text: trigram similarity in Postgres, so a search finds a part of a word, survives a typo, and stays fast on an index.

`text %> column` holds when some stretch of the column is similar enough to what was typed (pg_trgm word similarity), which a GIN
index with gin_trgm_ops answers without reading the table. The threshold is set on every connection by `install`.
"""
from typing import Any

from sqlalchemy import Boolean, ColumnElement, bindparam, event, or_, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import FunctionElement

def trigram_opclass(bind: Connection) -> str:
    """gin_trgm_ops dengan skema pemilik ekstensinya, supaya indeks trigram bisa dibuat dari skema mana pun, termasuk skema demo yang hanya melihat dirinya."""
    schema = bind.scalar(text("SELECT quote_ident(n.nspname) FROM pg_extension e JOIN pg_namespace n ON n.oid = e.extnamespace WHERE e.extname = 'pg_trgm'"))
    if schema is None:
        raise RuntimeError("Ekstensi pg_trgm belum terpasang; migrasi d4f6a8c0e215 memasangnya.")
    return f"{schema}.gin_trgm_ops"


# Ambang salah ketik: "minyk" terhadap "Minyak" (0,67) dan "capucino" (0,54) lolos; "minyk" terhadap "Mineral" (0,5) dan "Minyak" terhadap "Minuman" (0,43), yang hanya sama awalannya, tidak.
WORD_SIMILARITY_THRESHOLD = 0.51
# Potongan yang lebih pendek dari ini tidak dilayani indeks trigram, jadi pencocokan potongan utuh hanya untuk ketikan sepanjang ini.
MIN_FRAGMENT_LENGTH = 3


class _matches(FunctionElement):
    type = Boolean()
    inherit_cache = True
    name = "matches"


@compiles(_matches, "postgresql")
def _postgres(element, compiler, **kwargs) -> str:
    column, text = list(element.clauses)
    # Through the operator construct, so the driver's percent escaping is applied: psycopg reads a bare % as a placeholder.
    return compiler.process(column.op("%>")(text), **kwargs)


def _similar(column, typed: str) -> ColumnElement[bool]:
    return _matches(column, bindparam(None, typed, unique=True))


def _fragment(column, typed: str) -> ColumnElement[bool]:
    escaped = typed.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return column.ilike(bindparam(None, f"%{escaped}%", unique=True), escape="\\")


def contains(column, text: str) -> ColumnElement[bool]:
    """Kolom memuat ketikan sebagai potongan utuh ("ppuc" di "Cappuccino") atau cukup mirip untuk salah ketik; keduanya dilayani indeks trigram."""
    typed = text.strip()
    if len(typed) < MIN_FRAGMENT_LENGTH:
        return _similar(column, typed)
    return or_(_fragment(column, typed), _similar(column, typed))


def mentions(column, text: str) -> ColumnElement[bool]:
    """Hanya untuk daftar yang sudah dipersempit (misalnya satu sesi), karena potongan teks utuh seperti dua digit nomor nota ikut dicocokkan tanpa indeks."""
    typed = text.strip()
    return or_(_similar(column, typed), _fragment(column, typed))


def install(engine: Engine) -> None:
    if engine.dialect.name == "postgresql":
        event.listen(engine, "connect", _set_threshold)


def _set_threshold(dbapi_connection: Any, _record: Any) -> None:
    """Session level, and committed, like the time limit; a setting made inside a rolled-back transaction would be undone."""
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute(f"SET pg_trgm.word_similarity_threshold = {WORD_SIMILARITY_THRESHOLD}")
    finally:
        cursor.close()
    dbapi_connection.commit()
