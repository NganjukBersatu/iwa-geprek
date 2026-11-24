"""Reading the money trail the database writes (money_changes): by business day and branch, or by session."""
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.branches import branch_filter, outlet_names
from app.core.business_days import within
from app.core.money import decimal_of
from app.core.sorting import SqlSorting
from app.core.user_names import user_names
from app.models.outlet import Outlet
from app.models.user import User
from app.models.money_change import MoneyAction, MoneyChange, MoneySubject


class MoneyChangeOut(BaseModel):
    id: str
    outlet_id: str
    outlet_name: str | None
    business_day: date
    subject: MoneySubject
    subject_id: str
    subject_label: str
    session_id: str | None
    action: MoneyAction
    amount_before: Decimal
    amount_after: Decimal
    difference: Decimal
    fields: list[str]
    # True when the change came without a v2 account, such as from the legacy backend; user_name is then empty.
    by_system: bool
    user_name: str
    changed_at: datetime


class MoneyChangePageOut(BaseModel):
    items: list[MoneyChangeOut]
    total: int
    page: int


class MoneyChangeReportOut(MoneyChangePageOut):
    start: date
    end: date


def _out(rows: list[MoneyChange], db: Session) -> list[MoneyChangeOut]:
    """Names for the whole page in two queries."""
    people = user_names(db, (row.user_id for row in rows))
    branches = outlet_names(db, (row.outlet_id for row in rows))
    return [
        MoneyChangeOut(
            id=row.id,
            outlet_id=row.outlet_id,
            outlet_name=branches.get(row.outlet_id),
            business_day=row.business_day,
            subject=row.subject,
            subject_id=row.subject_id,
            subject_label=row.subject_label,
            session_id=row.session_id,
            action=row.action,
            amount_before=decimal_of(row.amount_before),
            amount_after=decimal_of(row.amount_after),
            difference=decimal_of(row.amount_after) - decimal_of(row.amount_before),
            fields=list(row.fields),
            by_system=row.user_id is None,
            user_name=people.get(row.user_id, "") if row.user_id else "",
            changed_at=row.changed_at,
        )
        for row in rows
    ]


SORTING = SqlSorting(
    columns={
        "business_day": MoneyChange.business_day,
        "subject": MoneyChange.subject,
        "action": MoneyChange.action,
        "outlet": select(Outlet.name).where(Outlet.id == MoneyChange.outlet_id).scalar_subquery(),
        "amount_before": MoneyChange.amount_before,
        "amount_after": MoneyChange.amount_after,
        "difference": MoneyChange.amount_after - MoneyChange.amount_before,
        "user": select(func.coalesce(User.name, User.username)).where(User.id == MoneyChange.user_id).scalar_subquery(),
        "changed_at": MoneyChange.changed_at,
    },
    default=(MoneyChange.business_day.desc(), MoneyChange.changed_at.desc()),
    tiebreak=MoneyChange.id,
)


def _page(db: Session, filters: list, order: list, page: int, size: int) -> MoneyChangePageOut:
    total = db.scalar(select(func.count()).select_from(MoneyChange).where(*filters)) or 0
    rows = list(db.scalars(select(MoneyChange).where(*filters).order_by(*order).offset((page - 1) * size).limit(size)).all())
    return MoneyChangePageOut(items=_out(rows, db), total=int(total), page=page)


def page_of(
    db: Session, start: date, end: date, outlet_id: str | None, subject: MoneySubject | None, sort: str | None, page: int, size: int
) -> MoneyChangeReportOut:
    """Newest business day first, and the latest change first within it; the id breaks ties so paging never skips a row."""
    filters = [*within(MoneyChange.business_day, start, end), *branch_filter(MoneyChange.outlet_id, outlet_id)]
    if subject is not None:
        filters.append(MoneyChange.subject == subject)
    found = _page(db, filters, SORTING.order_by(sort), page, size)
    return MoneyChangeReportOut(start=start, end=end, **found.model_dump())


def of_session(db: Session, session_id: str, outlet_id: str | None, sort: str | None, page: int, size: int) -> MoneyChangePageOut:
    """Everything changed in one session, deleted rows included, latest first; another branch's session reads as empty."""
    filters = [MoneyChange.session_id == session_id, *branch_filter(MoneyChange.outlet_id, outlet_id)]
    return _page(db, filters, SORTING.order_by(sort), page, size)
