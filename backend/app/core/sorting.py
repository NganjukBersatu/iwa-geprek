"""The one rule for ordering a list: `sort` is a column key the list offers, "-" in front for descending, empty for the list's own order."""
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Generic, TypeVar

from fastapi import Query
from sqlalchemy import ColumnElement, Enum, String, func

from app.core.errors import DomainError

PATTERN = r"^-?[a-z_][a-z0-9_]{0,39}$"
UNKNOWN_COLUMN = "Daftar ini tidak bisa diurutkan menurut kolom itu."
BAD_REQUEST = 400

# Query parameter of every sortable list.
Sort = Annotated[str | None, Query(pattern=PATTERN, description='A column key of the list; "-" in front for descending')]

SortValue = str | int | Decimal | date | datetime | bool
Row = TypeVar("Row")


@dataclass(frozen=True)
class Order:
    key: str
    descending: bool


def parse(sort: str | None, offered: Mapping[str, object]) -> Order | None:
    """None keeps the list's own order; a column the list does not offer is refused, never silently ignored."""
    if not sort:
        return None
    if not re.fullmatch(PATTERN, sort):
        raise DomainError(UNKNOWN_COLUMN, status=BAD_REQUEST)
    order = Order(sort.lstrip("-"), sort.startswith("-"))
    if order.key not in offered:
        raise DomainError(UNKNOWN_COLUMN, status=BAD_REQUEST)
    return order


@dataclass(frozen=True)
class SqlSorting:
    """A list read in pages: `columns` are what the database sorts by, chosen so an index serves them, and the id closes every order."""

    columns: Mapping[str, ColumnElement]
    default: tuple[ColumnElement, ...]
    tiebreak: ColumnElement

    def order_by(self, sort: str | None) -> list[ColumnElement]:
        order = parse(sort, self.columns)
        if order is None:
            return [*self.default, self.tiebreak]
        column = _comparable(self.columns[order.key])
        return [(column.desc() if order.descending else column.asc()).nulls_last(), self.tiebreak]


def _comparable(column: ColumnElement) -> ColumnElement:
    """Text sorts without regard to case, the same as RowSorting, whatever the database collation."""
    kind = column.type
    return func.lower(column) if isinstance(kind, String) and not isinstance(kind, Enum) else column


@dataclass(frozen=True)
class RowSorting(Generic[Row]):
    """A report computed in full: `keys` read each offered column of a row, empty values sit last, and `identity` breaks ties."""

    keys: Mapping[str, Callable[[Row], SortValue | None]]
    identity: Callable[[Row], str]

    def apply(self, rows: list[Row], sort: str | None) -> list[Row]:
        order = parse(sort, self.keys)
        if order is None:
            return rows
        read = self.keys[order.key]
        valued: list[tuple[SortValue, Row]] = []
        empty: list[Row] = []
        for row in rows:
            value = read(row)
            if value is None:
                empty.append(row)
            else:
                valued.append((value.casefold() if isinstance(value, str) else value, row))
        valued.sort(key=lambda pair: self.identity(pair[1]))
        valued.sort(key=lambda pair: pair[0], reverse=order.descending)
        return [row for _, row in valued] + sorted(empty, key=self.identity)
