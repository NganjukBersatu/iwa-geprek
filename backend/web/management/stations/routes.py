from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.orders.open_bills_visibility import show_open_bills
from app.core.auth import AnyOf, readable_outlet_id, require_gate, require_permission, writable_outlet_id
from app.core.branches import branch_ids_in_scope
from app.core.database import get_db
from app.core.date_range import Day
from app.core.errors import DomainError
from app.core.orders import station_setup, stations
from app.models.user import User
from web.management.reports import gates
from web.management.stations import service
from web.management.stations.schemas import (
    StationBranchesIn,
    StationBranchCopyIn,
    StationBranchOut,
    CategoryBranchStationIn,
    CategoryStationIn,
    StationInterveneIn,
    StationMonitorOut,
    StationPerformanceOut,
    StationSetupOut,
    StationCreateIn,
    ManagedStationOut,
    StationPatchIn,
    StationRolesIn,
    StationRolesOut,
    MenuTargetDetailOut,
    MenuTargetIn,
    MenuTargetPageOut,
    StationTaskOut,
)

# Semua bacaan di sini tidak di-cache: pantauan mengikuti sinyal live dan angka berubah di setiap langkah tablet.
# Bill yang belum dibayar sudah dikerjakan dapur, jadi laporan kerja stasiun ikut menghitungnya.
router = APIRouter(tags=["v2-stations-manage"], dependencies=[Depends(show_open_bills)])

MONITOR_GATE = AnyOf((station_setup.PERMISSION_MANAGE, stations.PERMISSION_INTERVENE))
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100
MAX_SEARCH_LENGTH = 100

may_manage = require_permission(station_setup.PERMISSION_MANAGE)


def _failed(error: DomainError) -> HTTPException:
    return HTTPException(status_code=error.status, detail=error.message)


def _written(db: Session, write) -> Response:
    try:
        write()
        db.commit()
    except DomainError as error:
        db.rollback()
        raise _failed(error) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/station-monitor", response_model=StationMonitorOut)
def monitor(outlet_id: str | None = Depends(readable_outlet_id), db: Session = Depends(get_db), _: User = Depends(require_gate(MONITOR_GATE))):
    return service.monitor(db, outlet_id)


@router.post("/station-tasks/{task_id}:intervene", response_model=StationTaskOut)
def intervene(
    task_id: str,
    body: StationInterveneIn,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(stations.PERMISSION_INTERVENE)),
):
    actor = stations.Actor(user_id=user.id, reason=body.reason.strip())
    scope = branch_ids_in_scope(db, outlet_id)
    steps = {"start": stations.start, "finish": stations.finish, "undo": stations.undo}
    try:
        steps[body.action](db, actor, scope, [task_id], body.seen)
        return service.task_detail(db, outlet_id, task_id)
    except DomainError as error:
        raise _failed(error) from error


@router.get("/station-tasks/{task_id}", response_model=StationTaskOut)
def task_detail(task_id: str, outlet_id: str | None = Depends(readable_outlet_id), db: Session = Depends(get_db), _: User = Depends(require_gate(MONITOR_GATE))):
    try:
        return service.task_detail(db, outlet_id, task_id)
    except DomainError as error:
        raise _failed(error) from error


@router.get("/station-performance", response_model=StationPerformanceOut)
def performance(
    start: Day | None = Query(None),
    end: Day | None = Query(None),
    station_id: str | None = Query(None),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_gate(gates.STATION_PERFORMANCE)),
):
    try:
        return service.performance(db, start, end, outlet_id, station_id)
    except DomainError as error:
        raise _failed(error) from error


@router.get("/menu-targets", response_model=MenuTargetPageOut)
def targets(
    start: Day | None = Query(None),
    end: Day | None = Query(None),
    search: str | None = Query(None, max_length=MAX_SEARCH_LENGTH),
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(may_manage),
):
    try:
        return service.targets(db, start, end, outlet_id, (search or "").strip() or None, page, size)
    except DomainError as error:
        raise _failed(error) from error


@router.get("/menu-targets/{menu_id}", response_model=MenuTargetDetailOut)
def target_detail(
    menu_id: str,
    start: Day | None = Query(None),
    end: Day | None = Query(None),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(may_manage),
):
    try:
        return service.target_detail(db, start, end, outlet_id, menu_id)
    except DomainError as error:
        raise _failed(error) from error


@router.patch("/menu-targets/{menu_id}", status_code=status.HTTP_204_NO_CONTENT)
def set_target(menu_id: str, body: MenuTargetIn, db: Session = Depends(get_db), _: User = Depends(may_manage)):
    return _written(db, lambda: station_setup.set_menu_target(db, menu_id, body.target_seconds))


@router.patch("/menu-targets/{menu_id}/branch-setting", status_code=status.HTTP_204_NO_CONTENT)
def set_branch_target(menu_id: str, body: MenuTargetIn, outlet_id: str = Depends(writable_outlet_id), db: Session = Depends(get_db), _: User = Depends(may_manage)):
    return _written(db, lambda: station_setup.set_menu_target_for_branch(db, outlet_id, menu_id, body.target_seconds))


@router.get("/stations", response_model=StationSetupOut)
def setup(outlet_id: str | None = Depends(readable_outlet_id), db: Session = Depends(get_db), _: User = Depends(may_manage)):
    return service.setup(db, outlet_id)


@router.post("/stations", response_model=ManagedStationOut, status_code=status.HTTP_201_CREATED)
def create_station(body: StationCreateIn, db: Session = Depends(get_db), _: User = Depends(may_manage)):
    try:
        station = station_setup.create_station(db, body.name, body.kind, body.target_seconds)
        db.commit()
    except DomainError as error:
        db.rollback()
        raise _failed(error) from error
    return next(row for row in service.setup(db, None).stations if row.id == station.id)


@router.patch("/stations/{station_id}", status_code=status.HTTP_204_NO_CONTENT)
def update_station(station_id: str, body: StationPatchIn, db: Session = Depends(get_db), _: User = Depends(may_manage)):
    def write() -> None:
        current = next((row for row in service.setup(db, None).stations if row.id == station_id), None)
        if current is None:
            raise DomainError(station_setup.STATION_NOT_FOUND, status=station_setup.NOT_FOUND)
        sent = body.model_fields_set
        station_setup.update_station(
            db,
            station_id,
            body.name if "name" in sent and body.name is not None else current.name,
            body.kind if "kind" in sent and body.kind is not None else current.kind,
            body.target_seconds if "target_seconds" in sent else current.target_seconds,
        )

    return _written(db, write)


@router.delete("/stations/{station_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_station(station_id: str, db: Session = Depends(get_db), _: User = Depends(may_manage)):
    return _written(db, lambda: station_setup.delete_station(db, station_id))


@router.get("/stations/{station_id}/branches", response_model=list[StationBranchOut])
def station_branches(station_id: str, outlet_id: str | None = Depends(readable_outlet_id), db: Session = Depends(get_db), _: User = Depends(may_manage)):
    try:
        return service.station_branches(db, station_id, outlet_id)
    except DomainError as error:
        raise _failed(error) from error


@router.put("/stations/{station_id}/branches", status_code=status.HTTP_204_NO_CONTENT)
def set_station_branches(station_id: str, body: StationBranchesIn, db: Session = Depends(get_db), user: User = Depends(may_manage)):
    return _written(db, lambda: service.set_station_branches(db, user, station_id, body))


@router.get("/stations/{station_id}/roles", response_model=StationRolesOut)
def station_roles(station_id: str, db: Session = Depends(get_db), _: User = Depends(may_manage)):
    try:
        return StationRolesOut(role_ids=station_setup.station_role_ids(db, station_id))
    except DomainError as error:
        raise _failed(error) from error


@router.put("/stations/{station_id}/roles", status_code=status.HTTP_204_NO_CONTENT)
def set_station_roles(station_id: str, body: StationRolesIn, db: Session = Depends(get_db), _: User = Depends(may_manage)):
    return _written(db, lambda: station_setup.set_station_roles(db, station_id, tuple(body.role_ids)))


@router.patch("/category-stations/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def set_category(category_id: str, body: CategoryStationIn, db: Session = Depends(get_db), _: User = Depends(may_manage)):
    return _written(db, lambda: station_setup.set_category_station(db, category_id, body.station_id))


@router.patch("/category-stations/{category_id}/branch-setting", status_code=status.HTTP_204_NO_CONTENT)
def set_category_branch(category_id: str, body: CategoryBranchStationIn, outlet_id: str = Depends(writable_outlet_id), db: Session = Depends(get_db), _: User = Depends(may_manage)):
    return _written(db, lambda: station_setup.set_category_for_branch(db, outlet_id, category_id, body.follows_default, body.station_id))


@router.post("/stations/{station_id}/branches:copy", status_code=status.HTTP_204_NO_CONTENT)
def copy_station_branches(station_id: str, body: StationBranchCopyIn, db: Session = Depends(get_db), user: User = Depends(may_manage)):
    return _written(db, lambda: service.copy_to_branches(db, user, station_id, body))
