"""WIB times of day worked out inside the database so a report groups in SQL; the day a row belongs to is its stored business_day."""
from sqlalchemy import Integer, Numeric
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import FunctionElement

from app.core.clock import WIB_OFFSET_HOURS


class wib_hour(FunctionElement):
    """The WIB hour (0 to 23) of a UTC timestamp."""

    type = Integer()
    inherit_cache = True
    name = "wib_hour"


@compiles(wib_hour, "postgresql")
def _postgres_hour(element, compiler, **kwargs) -> str:
    return f"(extract(hour from (({compiler.process(element.clauses, **kwargs)}) AT TIME ZONE 'UTC') + interval '{WIB_OFFSET_HOURS} hours')::integer)"


class wib_minute(FunctionElement):
    """The minute (0 to 59) within the WIB hour of a UTC timestamp."""

    type = Integer()
    inherit_cache = True
    name = "wib_minute"


@compiles(wib_minute, "postgresql")
def _postgres_minute(element, compiler, **kwargs) -> str:
    return f"(extract(minute from ({compiler.process(element.clauses, **kwargs)}) AT TIME ZONE 'UTC')::integer)"


class seconds_between(FunctionElement):
    """Seconds from the first timestamp to the second, fraction included."""

    type = Numeric()
    inherit_cache = True
    name = "seconds_between"


@compiles(seconds_between, "postgresql")
def _postgres_seconds(element, compiler, **kwargs) -> str:
    first, second = list(element.clauses)
    return f"extract(epoch from (({compiler.process(second, **kwargs)}) - ({compiler.process(first, **kwargs)})))"
