from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Integer, and_, cast, func, literal, select
from sqlalchemy.orm import Session

from app.core.catalog.menu import CATEGORY_KIND
from app.core.search import contains
from app.core.sql_time import seconds_between
from app.models.cash_session import CashSession, CashSessionStatus
from app.models.category import Category
from app.models.menu_item import MenuItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.station import CategoryBranchStation, CategoryStation, Station, StationMenuStat, StationUserStat, StationTask, StationTaskStep

LATE_LIST_LIMIT = 50
RATIO_STEP = Decimal("0.001")
SECONDS_STEP = Decimal("0.1")

Timing = tuple[int, Decimal | None, Decimal | None, Decimal | None]
EMPTY: Timing = (0, None, None, None)


def _sums(model) -> list:
    return [func.sum(model.tasks), func.sum(model.wait_seconds), func.sum(model.work_seconds), func.sum(model.targeted), func.sum(model.on_time)]


def _timing(row) -> Timing:
    tasks, wait, work, targeted, on_time = (int(value or 0) for value in row)
    if tasks <= 0:
        return EMPTY
    ratio = (Decimal(on_time) / Decimal(targeted)).quantize(RATIO_STEP) if targeted > 0 else None
    return tasks, (Decimal(wait) / tasks).quantize(SECONDS_STEP), (Decimal(work) / tasks).quantize(SECONDS_STEP), ratio


def _range(model, start: date, end: date, outlet_id: str | None) -> list:
    conditions = [model.business_day >= start, model.business_day <= end]
    if outlet_id:
        conditions.append(model.outlet_id == outlet_id)
    return conditions


def user_timing(db: Session, start: date, end: date, outlet_id: str | None, station_id: str | None) -> Timing:
    conditions = _range(StationUserStat, start, end, outlet_id)
    if station_id:
        conditions.append(StationUserStat.station_id == station_id)
    return _timing(db.execute(select(*_sums(StationUserStat)).where(*conditions)).one())


def user_timing_by_hour(db: Session, start: date, end: date, outlet_id: str | None, station_id: str | None) -> list[tuple[int, Timing]]:
    conditions = _range(StationUserStat, start, end, outlet_id)
    if station_id:
        conditions.append(StationUserStat.station_id == station_id)
    rows = db.execute(
        select(StationUserStat.hour, *_sums(StationUserStat)).where(*conditions).group_by(StationUserStat.hour).order_by(StationUserStat.hour)
    ).all()
    return [(int(row[0]), _timing(row[1:])) for row in rows]


def user_timing_by_person(db: Session, start: date, end: date, outlet_id: str | None, station_id: str | None) -> list[tuple[str | None, str, Timing]]:
    conditions = _range(StationUserStat, start, end, outlet_id)
    if station_id:
        conditions.append(StationUserStat.station_id == station_id)
    rows = db.execute(
        select(StationUserStat.user_id, StationUserStat.station_id, *_sums(StationUserStat))
        .where(*conditions)
        .group_by(StationUserStat.user_id, StationUserStat.station_id)
        .order_by(func.sum(StationUserStat.tasks).desc(), StationUserStat.station_id, StationUserStat.user_id)
    ).all()
    return [(row[0], row[1], _timing(row[2:])) for row in rows]


def menu_timing(db: Session, start: date, end: date, outlet_id: str | None, menu_ids: list[str]) -> dict[str, Timing]:
    if not menu_ids:
        return {}
    rows = db.execute(
        select(StationMenuStat.menu_item_id, *_sums(StationMenuStat))
        .where(*_range(StationMenuStat, start, end, outlet_id), StationMenuStat.menu_item_id.in_(menu_ids))
        .group_by(StationMenuStat.menu_item_id)
    ).all()
    return {row[0]: _timing(row[1:]) for row in rows}


def menu_timing_total(db: Session, start: date, end: date, outlet_id: str | None, menu_id: str) -> Timing:
    return _timing(db.execute(select(*_sums(StationMenuStat)).where(*_range(StationMenuStat, start, end, outlet_id), StationMenuStat.menu_item_id == menu_id)).one())


def menu_timing_by_outlet(db: Session, start: date, end: date, outlet_ids: list[str], menu_id: str) -> dict[str, Timing]:
    if not outlet_ids:
        return {}
    rows = db.execute(
        select(StationMenuStat.outlet_id, *_sums(StationMenuStat))
        .where(*_range(StationMenuStat, start, end, None), StationMenuStat.outlet_id.in_(outlet_ids), StationMenuStat.menu_item_id == menu_id)
        .group_by(StationMenuStat.outlet_id)
    ).all()
    return {row[0]: _timing(row[1:]) for row in rows}


def menu_timing_by_hour(db: Session, start: date, end: date, outlet_id: str | None, menu_id: str) -> list[tuple[int, Timing]]:
    rows = db.execute(
        select(StationMenuStat.hour, *_sums(StationMenuStat))
        .where(*_range(StationMenuStat, start, end, outlet_id), StationMenuStat.menu_item_id == menu_id)
        .group_by(StationMenuStat.hour)
        .order_by(StationMenuStat.hour)
    ).all()
    return [(int(row[0]), _timing(row[1:])) for row in rows]


def target_menus(db: Session, outlet_id: str | None, search: str | None, page: int, size: int) -> tuple[list[MenuItem], int]:
    # Hanya menu yang kategorinya dibuat di stasiun, menurut bawaan atau menurut cabang terpilih.
    by_default = select(CategoryStation.category_id)
    by_branch = select(CategoryBranchStation.category_id).where(CategoryBranchStation.outlet_id == (outlet_id or ""), CategoryBranchStation.station_id.is_not(None))
    conditions = [Category.kind == CATEGORY_KIND, MenuItem.category_id.in_(by_default.union(by_branch))]
    if search:
        conditions.append(contains(MenuItem.name, search))
    base = select(MenuItem).join(Category, Category.id == MenuItem.category_id).where(*conditions)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = db.scalars(base.order_by(MenuItem.name, MenuItem.id).offset((page - 1) * size).limit(size)).all()
    return list(rows), int(total)


def _active(outlet_ids: list[str]) -> tuple:
    running = select(CashSession.id).where(CashSession.status == CashSessionStatus.OPEN, CashSession.outlet_id.in_(outlet_ids))
    return (
        StationTask.outlet_id.in_(outlet_ids),
        StationTask.finished_at.is_(None),
        StationTask.arrived_at.is_not(None),
        StationTask.removed_at.is_(None),
        Order.cash_session_id.in_(running),
        Order.voided_at.is_(None),
        Order.served_at.is_(None),
    )


def _late(at: datetime):
    elapsed = seconds_between(StationTask.started_at, literal(at))
    return and_(StationTask.started_at.is_not(None), StationTask.target_seconds.is_not(None), elapsed > StationTask.target_seconds), elapsed


def monitor_cells(db: Session, outlet_ids: list[str], at: datetime) -> list[tuple[str, str, int, int]]:
    if not outlet_ids:
        return []
    late, _ = _late(at)
    rows = db.execute(
        select(StationTask.outlet_id, StationTask.station_id, func.count(), func.count().filter(late))
        .join(Order, Order.id == StationTask.order_id)
        .where(*_active(outlet_ids))
        .group_by(StationTask.outlet_id, StationTask.station_id)
        .order_by(StationTask.outlet_id, StationTask.station_id)
    ).all()
    return [(row[0], row[1], int(row[2]), int(row[3])) for row in rows]


def late_tasks(db: Session, outlet_ids: list[str], at: datetime) -> list:
    if not outlet_ids:
        return []
    late, elapsed = _late(at)
    overdue = elapsed - StationTask.target_seconds
    return db.execute(
        select(StationTask, Order, OrderItem.menu_item_name, OrderItem.qty, Station.name, cast(overdue, Integer))
        .join(Order, Order.id == StationTask.order_id)
        .join(OrderItem, OrderItem.id == StationTask.order_item_id)
        .join(Station, Station.id == StationTask.station_id)
        .where(*_active(outlet_ids), late)
        .order_by(overdue.desc(), StationTask.id)
        .limit(LATE_LIST_LIMIT)
    ).all()


def task_steps(db: Session, task_id: str) -> list[StationTaskStep]:
    return list(db.scalars(select(StationTaskStep).where(StationTaskStep.task_id == task_id).order_by(StationTaskStep.at, StationTaskStep.id)).all())
