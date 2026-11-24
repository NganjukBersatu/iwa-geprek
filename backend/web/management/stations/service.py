from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.branches import branch_ids_in_scope, outlet_names, outlets_in_scope
from app.core.catalog.menu import CATEGORY_KIND
from app.core.clock import now
from app.core.errors import DomainError
from app.core.orders import cancellations, reading, station_branch_settings, station_setup, stations
from app.core.user_names import user_names
from app.models.category import Category
from app.models.menu_item import MenuItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.user import User
from app.models.station import CategoryBranchStation, CategoryStation, MenuBranchTarget, MenuTarget, Station, StationTask
from web.management.reports.common import month_to_date
from web.management.stations import repository
from web.management.stations.schemas import (
    CategoryBranchOut,
    StationBranchCopyIn,
    StationBranchesIn,
    StationBranchOut,
    StationCategoryOut,
    StationHourOut,
    StationLateTaskOut,
    StationMonitorBranchOut,
    StationMonitorCellOut,
    StationMonitorOut,
    StationPerformanceOut,
    StationNameOut,
    StationSetupOut,
    StationUserTimingOut,
    ManagedStationOut,
    StationStepOut,
    MenuTargetBranchOut,
    MenuTargetDetailOut,
    MenuTargetPageOut,
    MenuTargetRowOut,
    StationTaskOut,
    StationTimingOut,
)

NOT_FOUND = 404
TASK_NOT_FOUND = "Item tidak ditemukan."
MENU_NOT_FOUND = "Menu tidak ditemukan."
OTHER_BRANCH = "Akun ini hanya boleh mengatur cabangnya sendiri."
FORBIDDEN = 403


def _timing_out(timing: repository.Timing) -> dict:
    tasks, wait, work, ratio = timing
    return {"tasks": tasks, "average_wait_seconds": wait, "average_work_seconds": work, "on_time_ratio": ratio}


def _station_rows(db: Session, outlet_id: str | None) -> list[ManagedStationOut]:
    setup = station_setup.setup_of(db, outlet_id or "")
    categories: dict[str, list[str]] = {}
    rows = db.execute(
        select(Category.name, CategoryStation.station_id).join(CategoryStation, CategoryStation.category_id == Category.id).order_by(Category.name, Category.id)
    ).all()
    for name, station_id in rows:
        categories.setdefault(station_id, []).append(name)
    branch = outlet_id is not None
    return [
        ManagedStationOut(
            id=entry.station.id,
            name=entry.station.name,
            kind=entry.station.kind,
            target_seconds=entry.station.target_seconds,
            used=entry.used if branch else True,
            branch_target_seconds=entry.target_seconds if branch and entry.target_seconds != entry.station.target_seconds else None,
            categories=categories.get(entry.station.id, []),
        )
        for entry in setup.stations.values()
    ]


def station_branches(db: Session, station_id: str, outlet_id: str | None) -> list[StationBranchOut]:
    outlets = outlets_in_scope(db, outlet_id)
    choices = station_setup.branch_choices(db, station_id, [outlet.id for outlet in outlets])
    return [
        StationBranchOut(outlet_id=outlet.id, outlet_name=outlet.name, used=choices[outlet.id].used, target_seconds=choices[outlet.id].target_seconds, reminder_seconds=choices[outlet.id].reminder_seconds, role_ids=list(choices[outlet.id].role_ids or ()))
        for outlet in outlets
    ]


def set_station_branches(db: Session, user: User, station_id: str, body: StationBranchesIn) -> None:
    locked = user.locked_outlet_id
    if locked and any(branch.outlet_id != locked for branch in body.branches):
        raise DomainError(OTHER_BRANCH, status=FORBIDDEN)
    station_setup.set_station_branches(
        db,
        station_id,
        [station_setup.BranchChange(branch.outlet_id, branch.target_seconds, branch.reminder_seconds, tuple(branch.role_ids) if branch.role_ids is not None else None) for branch in body.branches],
    )


def copy_to_branches(db: Session, user: User, station_id: str, body: StationBranchCopyIn) -> None:
    locked = user.locked_outlet_id
    if locked and (body.from_outlet_id != locked or any(outlet_id != locked for outlet_id in body.to_outlet_ids)):
        raise DomainError(OTHER_BRANCH, status=FORBIDDEN)
    station_branch_settings.copy_to_branches(db, station_id, body.from_outlet_id, body.to_outlet_ids)


def setup(db: Session, outlet_id: str | None) -> StationSetupOut:
    defaults = dict(db.execute(select(CategoryStation.category_id, CategoryStation.station_id)).all())
    exceptions = db.execute(
        select(CategoryBranchStation.category_id, CategoryBranchStation.outlet_id, CategoryBranchStation.station_id).where(
            *(() if outlet_id is None else (CategoryBranchStation.outlet_id == outlet_id,))
        )
    ).all()
    names = outlet_names(db, [row.outlet_id for row in exceptions])
    by_category: dict[str, list[CategoryBranchOut]] = {}
    for category_id, branch_id, station_id in exceptions:
        by_category.setdefault(category_id, []).append(CategoryBranchOut(outlet_id=branch_id, outlet_name=names.get(branch_id, ""), station_id=station_id))
    categories = [
        StationCategoryOut(
            id=category.id,
            name=category.name,
            station_id=defaults.get(category.id),
            branches=sorted(by_category.get(category.id, []), key=lambda branch: (branch.outlet_name, branch.outlet_id)),
        )
        for category in db.scalars(select(Category).where(Category.kind == CATEGORY_KIND).order_by(Category.name, Category.id)).all()
    ]
    return StationSetupOut(
        outlet_id=outlet_id,
        stations=_station_rows(db, outlet_id),
        categories=categories,
    )


def monitor(db: Session, outlet_id: str | None) -> StationMonitorOut:
    outlets = outlets_in_scope(db, outlet_id)
    ids = [outlet.id for outlet in outlets]
    at = now()
    cells = repository.monitor_cells(db, ids, at)
    by_outlet: dict[str, list[StationMonitorCellOut]] = {}
    for outlet, station_id, working, late in cells:
        by_outlet.setdefault(outlet, []).append(StationMonitorCellOut(station_id=station_id, working=working, late=late))
    names = {outlet.id: outlet.name for outlet in outlets}
    return StationMonitorOut(
        stations=_station_rows(db, outlet_id),
        branches=[
            StationMonitorBranchOut(outlet_id=outlet.id, outlet_name=outlet.name, cells=by_outlet.get(outlet.id, []))
            for outlet in outlets
        ],
        working=sum(cell[2] for cell in cells),
        late=sum(cell[3] for cell in cells),
        late_tasks=[
            StationLateTaskOut(
                task_id=task.id,
                order_id=order.id,
                receipt_number=order.receipt_number,
                table_no=order.table_no,
                customer_name=order.customer_name,
                outlet_name=names.get(order.outlet_id, ""),
                station_name=station_name,
                item=f"{qty}x {item_name}",
                stage=stations.stage_of(task),
                started_at=task.started_at,
                target_seconds=task.target_seconds,
                late_seconds=max(0, int(overdue or 0)),
            )
            for task, order, item_name, qty, station_name, overdue in repository.late_tasks(db, ids, at)
        ],
    )


def task_detail(db: Session, outlet_id: str | None, task_id: str) -> StationTaskOut:
    task = db.get(StationTask, task_id)
    if task is None or task.outlet_id not in branch_ids_in_scope(db, outlet_id):
        raise DomainError(TASK_NOT_FOUND, status=NOT_FOUND)
    order = db.get(Order, task.order_id)
    station = db.get(Station, task.station_id)
    if order is None or station is None:
        raise DomainError(TASK_NOT_FOUND, status=NOT_FOUND)
    item = db.get(OrderItem, task.order_item_id) if task.order_item_id else None
    options: list[str] = []
    if item is not None:
        options = [option.name for option in reading.lines_of(db, [order])[0].options.get(item.id, [])]
    steps = repository.task_steps(db, task.id)
    names = user_names(db, (step.user_id for step in steps if step.user_id))
    return StationTaskOut(
        task_id=task.id,
        order_id=order.id,
        receipt_number=order.receipt_number,
        table_no=order.table_no,
        customer_name=order.customer_name,
        order_created_at=order.created_at,
        outlet_name=outlet_names(db, [order.outlet_id]).get(order.outlet_id, ""),
        station_name=station.name,
        station_kind=station.kind,
        item=f"{item.qty}x {item.menu_item_name}" if item is not None else task.removed_label or "",
        note=item.note if item is not None else None,
        options=options,
        stage=stations.stage_of(task),
        arrived_at=task.arrived_at,
        started_at=task.started_at,
        finished_at=task.finished_at,
        target_seconds=task.target_seconds,
        removed=task.removed_at is not None,
        voided=order.voided_at is not None,
        locked=cancellations.has_pending(db, order.id),
        steps=[StationStepOut(step=step.step, by=names.get(step.user_id) if step.user_id else None, reason=step.reason, intervened=step.intervened, at=step.at) for step in steps],
    )


def performance(db: Session, start: date | None, end: date | None, outlet_id: str | None, station_id: str | None) -> StationPerformanceOut:
    start, end = month_to_date(start, end)
    people = repository.user_timing_by_person(db, start, end, outlet_id, station_id)
    names = user_names(db, (user_id for user_id, _, _ in people if user_id))
    ordered = db.execute(select(Station.id, Station.name).order_by(Station.position, Station.name, Station.id)).all()
    station_names = dict(ordered)
    return StationPerformanceOut(
        start=start,
        end=end,
        stations=[StationNameOut(id=station_id, name=name) for station_id, name in ordered],
        overall=StationTimingOut(**_timing_out(repository.user_timing(db, start, end, outlet_id, station_id))),
        by_hour=[StationHourOut(hour=hour, **_timing_out(timing)) for hour, timing in repository.user_timing_by_hour(db, start, end, outlet_id, station_id)],
        by_user=[
            StationUserTimingOut(user_id=user_id, name=names.get(user_id, "") if user_id else "", station_id=station, station_name=station_names.get(station, ""), **_timing_out(timing))
            for user_id, station, timing in people
        ],
    )


def targets(db: Session, start: date | None, end: date | None, outlet_id: str | None, search: str | None, page: int, size: int) -> MenuTargetPageOut:
    start, end = month_to_date(start, end)
    menus, total = repository.target_menus(db, outlet_id, search, page, size)
    ids = [menu.id for menu in menus]
    makers = station_setup.makers_of_menus(db, outlet_id or "", set(ids))
    station_names = dict(db.execute(select(Station.id, Station.name)).all())
    defaults = dict(db.execute(select(MenuTarget.menu_item_id, MenuTarget.target_seconds).where(MenuTarget.menu_item_id.in_(ids))).all()) if ids else {}
    own: dict[str, int] = {}
    if outlet_id and ids:
        own = dict(db.execute(select(MenuBranchTarget.menu_item_id, MenuBranchTarget.target_seconds).where(MenuBranchTarget.outlet_id == outlet_id, MenuBranchTarget.menu_item_id.in_(ids))).all())
    stats = repository.menu_timing(db, start, end, outlet_id, ids)
    return MenuTargetPageOut(
        start=start,
        end=end,
        items=[
            MenuTargetRowOut(
                menu_id=menu.id,
                name=menu.name,
                station_name=station_names.get(makers.get(menu.id) or ""),
                target_seconds=defaults.get(menu.id),
                branch_target_seconds=own.get(menu.id),
                **_timing_out(stats.get(menu.id, repository.EMPTY)),
            )
            for menu in menus
        ],
        total=total,
        page=page,
        size=size,
    )


def target_detail(db: Session, start: date | None, end: date | None, outlet_id: str | None, menu_id: str) -> MenuTargetDetailOut:
    menu = db.get(MenuItem, menu_id)
    if menu is None:
        raise DomainError(MENU_NOT_FOUND, status=NOT_FOUND)
    start, end = month_to_date(start, end)
    outlets = outlets_in_scope(db, outlet_id)
    ids = [outlet.id for outlet in outlets]
    own = dict(db.execute(select(MenuBranchTarget.outlet_id, MenuBranchTarget.target_seconds).where(MenuBranchTarget.menu_item_id == menu.id, MenuBranchTarget.outlet_id.in_(ids))).all()) if ids else {}
    per_outlet = repository.menu_timing_by_outlet(db, start, end, ids, menu.id)
    default = db.get(MenuTarget, menu.id)
    maker = station_setup.makers_of_menus(db, outlet_id or "", {menu.id}).get(menu.id)
    station = db.get(Station, maker) if maker else None
    return MenuTargetDetailOut(
        start=start,
        end=end,
        menu_id=menu.id,
        name=menu.name,
        station_name=station.name if station is not None else None,
        target_seconds=default.target_seconds if default is not None else None,
        overall=StationTimingOut(**_timing_out(repository.menu_timing_total(db, start, end, outlet_id, menu.id))),
        branches=[
            MenuTargetBranchOut(outlet_id=outlet.id, outlet_name=outlet.name, target_seconds=own.get(outlet.id), **_timing_out(per_outlet.get(outlet.id, repository.EMPTY)))
            for outlet in outlets
        ],
        by_hour=[StationHourOut(hour=hour, **_timing_out(timing)) for hour, timing in repository.menu_timing_by_hour(db, start, end, outlet_id, menu.id)],
    )
