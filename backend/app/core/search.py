"""The one way to search text: trigram similarity in Postgres, so a search finds a part of a word, survives a typo, and stays fast on an index.

`text %> column` holds when some stretch of the column is similar enough to what was typed (pg_trgm word similarity), which a GIN
index with gin_trgm_ops answers without reading the table. The threshold is set on every connection by `install`.
"""
from typing import Any

from sqlalchemy import Boolean, ColumnElement, bindparam, event, or_
from sqlalchemy.engine import Engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import FunctionElement

# How much of what was typed must be found in one stretch of the text: low enough for "ppuc" to find "Cappuccino" and for a typo to pass.
WORD_SIMILARITY_THRESHOLD = 0.3


class _matches(FunctionElement):
    type = Boolean()
    inherit_cache = True
    name = "matches"


@compiles(_matches, "postgresql")
def _postgres(element, compiler, **kwargs) -> str:
    column, text = list(element.clauses)
    # Through the operator construct, so the driver's percent escaping is applied: psycopg reads a bare % as a placeholder.
    return compiler.process(column.op("%>")(text), **kwargs)


def contains(column, text: str) -> ColumnElement[bool]:
    """Whether the column matches what a person typed; the text is a bound value, so no character acts as a wildcard."""
    return _matches(column, bindparam(None, text.strip(), unique=True))


def mentions(column, text: str) -> ColumnElement[bool]:
    """Hanya untuk daftar yang sudah dipersempit (misalnya satu sesi), karena potongan teks utuh seperti dua digit nomor nota ikut dicocokkan tanpa indeks."""
    typed = text.strip()
    escaped = typed.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return or_(contains(column, typed), column.ilike(bindparam(None, f"%{escaped}%", unique=True), escape="\\"))


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
