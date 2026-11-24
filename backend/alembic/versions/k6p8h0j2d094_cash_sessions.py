"""cash sessions: the table `shifts` held the cash sessions of the till, which is not what a shift is here (shift_codes, schedules, and attendance are the working shifts)

Revision ID: k6p8h0j2d094
Revises: j5o7g9i1c983
Create Date: 2026-11-06 15:00:00.000000

The table becomes `cash_sessions` and its enum type `cash_session_status`, so the name says what the rows are, like the `cash_session_id` columns that
already point at it. Constraint and index names that carry the old word are renamed to match. The trigger functions are text, so the ones that read or
sit on the table are written again with the new name, and the check at the end refuses to finish if any function still mentions `shifts`.

Every step looks first and acts only when the old name is still there, so a second run changes nothing. Down does nothing: the old name is not worth
restoring (the code no longer knows it), and a mistake after release is fixed with a forward migration.
"""
import logging
import re
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'k6p8h0j2d094'
down_revision: Union[str, Sequence[str], None] = 'j5o7g9i1c983'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = {'shifts': 'cash_sessions'}
ENUMS = {'shift_status': 'cash_session_status'}
OLD = 'shifts'
NEW = 'cash_sessions'
MAX_NAME_LENGTH = 63

OLD_TRIGGERS = ('shifts_business_day', 'shifts_business_day_cascade', 'shifts_money_change')
OLD_FUNCTIONS = ('shifts_business_day()', 'shifts_business_day_cascade()', 'shifts_money_change()')

FUNCTIONS = (
    """
CREATE OR REPLACE FUNCTION cash_sessions_business_day() RETURNS trigger AS $$
BEGIN
    NEW.business_day := wib_date(NEW.opened_at);
    RETURN NEW;
END $$ LANGUAGE plpgsql;
""",
    """
CREATE OR REPLACE FUNCTION orders_business_day() RETURNS trigger AS $$
BEGIN
    NEW.business_day := COALESCE(
        (SELECT s.business_day FROM cash_sessions s WHERE s.id = NEW.cash_session_id),
        CASE WHEN TG_OP = 'UPDATE' THEN OLD.business_day END,
        wib_date(NEW.created_at)
    );
    RETURN NEW;
END $$ LANGUAGE plpgsql;
""",
    """
CREATE OR REPLACE FUNCTION expenses_business_day() RETURNS trigger AS $$
BEGIN
    NEW.business_day := COALESCE(
        (SELECT s.business_day FROM cash_sessions s WHERE s.id = NEW.cash_session_id),
        CASE WHEN TG_OP = 'UPDATE' THEN OLD.business_day END,
        wib_date(NEW.created_at)
    );
    RETURN NEW;
END $$ LANGUAGE plpgsql;
""",
    """
CREATE OR REPLACE FUNCTION overpayments_business_day() RETURNS trigger AS $$
BEGIN
    NEW.business_day := COALESCE(
        (SELECT o.business_day FROM orders o WHERE o.id = NEW.order_id),
        (SELECT s.business_day FROM cash_sessions s WHERE s.id = NEW.cash_session_id),
        CASE WHEN TG_OP = 'UPDATE' THEN OLD.business_day END,
        wib_date(NEW.recorded_at)
    );
    RETURN NEW;
END $$ LANGUAGE plpgsql;
""",
    """
CREATE OR REPLACE FUNCTION cash_sessions_business_day_cascade() RETURNS trigger AS $$
BEGIN
    UPDATE orders SET business_day = NULL WHERE cash_session_id = NEW.id;
    UPDATE expenses SET business_day = NULL WHERE cash_session_id = NEW.id;
    RETURN NULL;
END $$ LANGUAGE plpgsql;
""",
    """
CREATE OR REPLACE FUNCTION money_change_late(p_shift TEXT, p_day DATE) RETURNS boolean AS $$
    SELECT CASE
        WHEN p_shift IS NULL THEN p_day < wib_date(now())
        ELSE COALESCE((SELECT s.status = 'CLOSED' FROM cash_sessions s WHERE s.id = p_shift), p_day < wib_date(now()))
    END
$$ LANGUAGE sql STABLE;
""",
    """
CREATE OR REPLACE FUNCTION cash_sessions_money_change() RETURNS trigger AS $$
DECLARE
    changed TEXT[] := '{}';
BEGIN
    IF TG_OP = 'DELETE' THEN
        PERFORM money_change_write(OLD.outlet_id, OLD.business_day, 'session', OLD.id, OLD.id, OLD.shift_code, 'delete', COALESCE(OLD.actual_cash, 0), 0, ARRAY['actual_cash']);
        RETURN NULL;
    END IF;
    IF OLD.status IS DISTINCT FROM 'CLOSED' THEN
        RETURN NULL;
    END IF;
    IF OLD.opening_cash IS DISTINCT FROM NEW.opening_cash THEN changed := array_append(changed, 'opening_cash'::text); END IF;
    IF OLD.actual_cash IS DISTINCT FROM NEW.actual_cash THEN changed := array_append(changed, 'actual_cash'::text); END IF;
    IF OLD.difference IS DISTINCT FROM NEW.difference THEN changed := array_append(changed, 'difference'::text); END IF;
    IF OLD.outlet_id IS DISTINCT FROM NEW.outlet_id THEN changed := array_append(changed, 'outlet'::text); END IF;
    IF OLD.business_day IS DISTINCT FROM NEW.business_day THEN changed := array_append(changed, 'business_day'::text); END IF;
    PERFORM money_change_compare('session', NEW.id, NEW.id, NEW.shift_code, OLD.outlet_id, OLD.business_day, COALESCE(OLD.actual_cash, 0),
        NEW.outlet_id, NEW.business_day, COALESCE(NEW.actual_cash, 0), 'update', changed);
    RETURN NULL;
END $$ LANGUAGE plpgsql;
""",
)

TRIGGERS = (
    "CREATE TRIGGER cash_sessions_business_day BEFORE INSERT OR UPDATE ON cash_sessions FOR EACH ROW EXECUTE FUNCTION cash_sessions_business_day()",
    "CREATE TRIGGER cash_sessions_business_day_cascade AFTER UPDATE OF business_day ON cash_sessions FOR EACH ROW WHEN (OLD.business_day IS DISTINCT FROM NEW.business_day) EXECUTE FUNCTION cash_sessions_business_day_cascade()",
    "CREATE TRIGGER cash_sessions_money_change AFTER UPDATE OR DELETE ON cash_sessions FOR EACH ROW EXECUTE FUNCTION cash_sessions_money_change()",
)

WORD = re.compile(r'(?<![A-Za-z0-9])shifts(?![A-Za-z0-9])')


def _exists(bind, name: str) -> bool:
    return bool(bind.scalar(sa.text("SELECT to_regclass(quote_ident(current_schema()) || '.' || :n) IS NOT NULL"), {'n': f'"{name}"'}))


def _rename_type(bind) -> None:
    for old, new in ENUMS.items():
        query = "SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = :n AND typnamespace = current_schema()::regnamespace)"
        if bind.scalar(sa.text(query), {'n': old}) and not bind.scalar(sa.text(query), {'n': new}):
            op.execute(f'ALTER TYPE "{old}" RENAME TO "{new}"')


def _rename_names(bind) -> list[str]:
    """Constraint and index names that carry the old word, rebuilt with the new one; a name that is too long or already taken is left as it is."""
    skipped: list[str] = []
    taken = {row[0] for row in bind.execute(sa.text("SELECT relname::text FROM pg_class WHERE relnamespace = current_schema()::regnamespace"))}
    taken |= {row[0] for row in bind.execute(sa.text("SELECT conname::text FROM pg_constraint c JOIN pg_class t ON t.oid = c.conrelid WHERE t.relnamespace = current_schema()::regnamespace"))}

    constraints = bind.execute(sa.text(
        "SELECT c.conname::text, t.relname::text FROM pg_constraint c JOIN pg_class t ON t.oid = c.conrelid "
        "WHERE t.relnamespace = current_schema()::regnamespace AND c.conname ~ '(^|[^A-Za-z0-9])shifts([^A-Za-z0-9]|$)'")).all()
    for name, table in constraints:
        new = WORD.sub(NEW, name)
        if new == name or len(new) > MAX_NAME_LENGTH or new in taken:
            skipped.append(f'{name} -> {new}')
            continue
        op.execute(f'ALTER TABLE "{table}" RENAME CONSTRAINT "{name}" TO "{new}"')
        taken.discard(name)
        taken.add(new)

    indexes = bind.execute(sa.text(
        "SELECT ic.relname::text FROM pg_index i JOIN pg_class ic ON ic.oid = i.indexrelid JOIN pg_class t ON t.oid = i.indrelid "
        "WHERE t.relnamespace = current_schema()::regnamespace AND ic.relname ~ '(^|[^A-Za-z0-9])shifts([^A-Za-z0-9]|$)' "
        "AND NOT EXISTS (SELECT 1 FROM pg_constraint c WHERE c.conindid = i.indexrelid)")).all()
    for (name,) in indexes:
        new = WORD.sub(NEW, name)
        if new == name or len(new) > MAX_NAME_LENGTH or new in taken:
            skipped.append(f'{name} -> {new}')
            continue
        op.execute(f'ALTER INDEX "{name}" RENAME TO "{new}"')
        taken.discard(name)
        taken.add(new)
    return skipped


def _verify(bind) -> None:
    if not _exists(bind, NEW):
        raise RuntimeError(f'table {NEW} is missing')
    if _exists(bind, OLD):
        raise RuntimeError(f'table {OLD} still exists')
    stale = [row[0] for row in bind.execute(sa.text(
        "SELECT proname::text FROM pg_proc WHERE pronamespace = current_schema()::regnamespace AND prosrc ~ '\\mshifts\\M' ORDER BY 1"))]
    if stale:
        raise RuntimeError(f'functions that still mention {OLD}: {", ".join(stale)}')


def upgrade() -> None:
    bind = op.get_bind()
    op.execute("SET LOCAL lock_timeout = '5s'")

    for name in OLD_TRIGGERS:
        op.execute(f'DROP TRIGGER IF EXISTS "{name}" ON "{OLD}"')
        op.execute(f'DROP TRIGGER IF EXISTS "{name}" ON "{NEW}"')

    _rename_type(bind)
    if _exists(bind, OLD) and not _exists(bind, NEW):
        op.execute(f'ALTER TABLE "{OLD}" RENAME TO "{NEW}"')
    skipped = _rename_names(bind)

    for function in FUNCTIONS:
        op.execute(function)
    for trigger in TRIGGERS:
        name = trigger.split()[2]
        op.execute(f'DROP TRIGGER IF EXISTS "{name}" ON "{NEW}"')
        op.execute(trigger)
    for function in OLD_FUNCTIONS:
        op.execute(f'DROP FUNCTION IF EXISTS {function}')

    _verify(bind)
    if skipped:
        logging.getLogger('alembic.runtime.migration').warning('names kept as they were (too long or already taken): %s', '; '.join(skipped))


def downgrade() -> None:
    # The old name is not restored: the code no longer knows it, and a mistake after release is fixed with a forward migration.
    pass
