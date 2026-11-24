from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.orders.open_bills_visibility import show_open_bills
from app.core.auth import require_permission
from app.core import page_cursor
from app.core.database import get_db
from app.core.devices import device_stations
from app.core.errors import DomainError
from app.core.orders import station_recipe, station_setup, station_workers, stations
from app.core.user_names import user_names
from app.models.cancellation_request import CancellationRequest, CancellationStatus
from app.models.device import Device
from app.models.user import User
from app.models.station import StationKind, StationTask
from app.operational.device import tablet

# Bill yang belum dibayar sudah dikerjakan dapur, jadi stasiun melihatnya.
router = APIRouter(tags=["v2-operational-stations"], dependencies=[Depends(show_open_bills)])

MAX_RECIPE_LINES = 100
# Satu uuid beserta koma pemisahnya.
ID_LENGTH = 37


class BoardStationOut(BaseModel):
    id: str
    name: str
    kind: StationKind
    target_seconds: int | None
    # Jeda bunyi pengingat dalam detik; 0 berarti pengingat mati di stasiun ini.
    reminder_seconds: int
    # Stasiun ini ditetapkan ke tablet yang meminta; tablet menampilkan satu tab untuk setiap stasiun yang dipegang.
    held: bool


class BoardTaskOut(BaseModel):
    id: str
    station_id: str
    stage: stations.Stage
    arrived_at: datetime | None
    started_at: datetime | None
    started_by: str | None
    finished_at: datetime | None
    # Kosong pada menu yang selesai berarti ditutup sistem.
    finished_by: str | None
    printed_at: datetime | None
    target_seconds: int | None
    correction: str | None
    removed_at: datetime | None
    acknowledged: bool


class BoardLineOut(BaseModel):
    # Kosong untuk baris yang dihapus koreksi; name berisi apa yang dihapus.
    id: str | None
    menu_item_id: str | None
    name: str
    qty: int
    note: str | None
    options: list[str]
    tasks: list[BoardTaskOut]


class BoardRequestOut(BaseModel):
    id: str
    requested_by_id: str
    requested_by: str
    reason: str | None
    created_at: datetime


class BoardDecisionOut(BaseModel):
    id: str
    approved: bool
    decided_by: str
    note: str | None
    decided_at: datetime


class StationBoardOrderOut(BaseModel):
    id: str
    receipt_number: str | None
    customer_name: str | None
    table_no: str | None
    order_type: str
    total: Decimal
    created_at: datetime
    voided: bool
    lines: list[BoardLineOut]
    cancellation: BoardRequestOut | None
    decision: BoardDecisionOut | None
    # Sesi kasir pesanan ini sudah ditutup, sedangkan menunya belum selesai di stasiun.
    left_behind: bool
    session_cashier: str | None


class StationBoardOut(BaseModel):
    orders: list[StationBoardOrderOut]
    truncated: bool


class StationStepIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_ids: list[str] = Field(min_length=1, max_length=stations.MAX_STEP_TASKS)
    # Tahap yang terlihat di tablet; yang sudah basi ditolak karena tablet lain lebih dulu.
    seen: stations.Stage
    # Karyawan yang mengerjakan menu ini; kosong berarti akun yang login di tablet.
    worker_id: str | None = Field(None, min_length=1, max_length=64)


class StationAcknowledgeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_ids: list[str] = Field(min_length=1, max_length=stations.MAX_STEP_TASKS)


class StationIngredientOut(BaseModel):
    name: str
    unit: str | None
    per_portion: Decimal
    total: Decimal


class StationRecipeOut(BaseModel):
    portions: int
    ingredients: list[StationIngredientOut]
    without_recipe: list[str]


def _task_out(entry: stations.BoardTask, names: dict[str, str]) -> BoardTaskOut:
    task = entry.task
    return BoardTaskOut(
        id=task.id,
        station_id=task.station_id,
        stage=stations.stage_of(task),
        arrived_at=task.arrived_at,
        started_at=task.started_at,
        started_by=names.get(task.started_by) if task.started_by else None,
        finished_at=task.finished_at,
        finished_by=names.get(task.finished_by) if task.finished_by else None,
        printed_at=task.printed_at,
        target_seconds=task.target_seconds,
        correction=task.correction,
        removed_at=task.removed_at,
        acknowledged=task.acknowledged_at is not None,
    )


def _line_out(line: stations.BoardLine, names: dict[str, str]) -> BoardLineOut:
    tasks = [_task_out(entry, names) for entry in line.tasks]
    if line.item is None:
        label = line.tasks[0].task.removed_label if line.tasks else None
        return BoardLineOut(id=None, menu_item_id=None, name=label or "", qty=0, note=None, options=[], tasks=tasks)
    item = line.item
    return BoardLineOut(id=item.id, menu_item_id=item.menu_item_id, name=item.menu_item_name, qty=item.qty, note=item.note, options=line.options, tasks=tasks)


def _request_out(row: CancellationRequest | None, names: dict[str, str]) -> BoardRequestOut | None:
    if row is None:
        return None
    return BoardRequestOut(id=row.id, requested_by_id=row.requested_by_id, requested_by=names.get(row.requested_by_id, ""), reason=row.reason, created_at=row.created_at)


def _decision_out(row: CancellationRequest | None, names: dict[str, str]) -> BoardDecisionOut | None:
    if row is None or row.decided_at is None:
        return None
    return BoardDecisionOut(
        id=row.id,
        approved=row.status == CancellationStatus.APPROVED,
        decided_by=names.get(row.decided_by_id or "", ""),
        note=row.manager_note,
        decided_at=row.decided_at,
    )


def _orders_out(db: Session, entries: list[stations.BoardOrder]) -> list[StationBoardOrderOut]:
    ids: set[str] = set()
    for entry in entries:
        ids.update(task.task.started_by for line in entry.lines for task in line.tasks if task.task.started_by)
        ids.update(task.task.finished_by for line in entry.lines for task in line.tasks if task.task.finished_by)
        if entry.session_cashier_id:
            ids.add(entry.session_cashier_id)
        if entry.pending is not None:
            ids.add(entry.pending.requested_by_id)
        if entry.decided is not None and entry.decided.decided_by_id:
            ids.add(entry.decided.decided_by_id)
    names = user_names(db, ids)
    return [
        StationBoardOrderOut(
            id=entry.order.id,
            receipt_number=entry.order.receipt_number,
            customer_name=entry.order.customer_name,
            table_no=entry.order.table_no,
            order_type=entry.order.order_type,
            total=entry.order.total,
            created_at=entry.order.created_at,
            voided=entry.order.voided_at is not None,
            lines=[_line_out(line, names) for line in entry.lines],
            cancellation=_request_out(entry.pending, names),
            decision=_decision_out(entry.decided, names),
            left_behind=entry.left_behind,
            session_cashier=names.get(entry.session_cashier_id) if entry.session_cashier_id else None,
        )
        for entry in entries
    ]


def _failed(error: DomainError) -> HTTPException:
    return HTTPException(status_code=error.status, detail=error.message)


@router.get("/stations", response_model=list[BoardStationOut])
def list_stations(device: Device = Depends(tablet), db: Session = Depends(get_db)):
    setup = station_setup.setup_of(db, device.outlet_id)
    held = set(device_stations.held_ids(db, [device.id]).get(device.id, []))
    return [
        BoardStationOut(id=entry.station.id, name=entry.station.name, kind=entry.station.kind, target_seconds=entry.target_seconds, reminder_seconds=entry.reminder_seconds, held=entry.station.id in held)
        for entry in setup.stations.values()
        if entry.used
    ]


@router.get("/station-board", response_model=StationBoardOut)
def board(device: Device = Depends(tablet), db: Session = Depends(get_db)):
    found = stations.board(db, device.outlet_id)
    return StationBoardOut(orders=_orders_out(db, found.orders), truncated=found.truncated)


class StationHistoryEntryOut(BaseModel):
    task_id: str
    order_id: str


class StationHistoryOut(BaseModel):
    # Terbaru dulu; rincian setiap pesanan ada di orders, sekali per pesanan.
    entries: list[StationHistoryEntryOut]
    orders: list[StationBoardOrderOut]
    # Kosong berarti halaman terakhir.
    next_cursor: str | None


# Tidak di-cache: Riwayat berubah di setiap langkah stasiun, dan tablet memuat ulang lewat sinyal /live.
@router.get("/station-history", response_model=StationHistoryOut)
def history(
    station_id: str = Query(min_length=1, max_length=ID_LENGTH),
    cursor: str | None = Query(None, max_length=page_cursor.MAX_CURSOR_LENGTH),
    limit: int = Query(page_cursor.DEFAULT_LIMIT, ge=1, le=page_cursor.MAX_LIMIT),
    part: stations.HistoryPart | None = Query(None, description="moving: pesanannya masih berjalan; done: sudah tuntas atau dibatalkan; kosong: semuanya"),
    device: Device = Depends(tablet),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(stations.PERMISSION_WORK)),
):
    try:
        found = stations.history(db, device.outlet_id, station_id, cursor, limit, part)
    except DomainError as error:
        raise _failed(error) from error
    return StationHistoryOut(
        entries=[StationHistoryEntryOut(task_id=task_id, order_id=order_id) for task_id, order_id in found.entries],
        orders=_orders_out(db, found.orders),
        next_cursor=found.next_cursor,
    )


def _stepped(db: Session, orders) -> list[StationBoardOrderOut]:
    return _orders_out(db, stations.board_of(db, orders))


def _worker_of(db: Session, device: Device, user: User, body: StationStepIn) -> stations.Actor:
    """Pelaku yang dicatat untuk langkah ini; yang dipilih diperiksa ulang terhadap stasiun menu yang dikerjakan."""
    if not body.worker_id or body.worker_id == user.id:
        return stations.Actor(user_id=user.id)
    station_id = db.scalar(select(StationTask.station_id).where(StationTask.id.in_(body.task_ids), StationTask.outlet_id == device.outlet_id).limit(1))
    if station_id is None:
        return stations.Actor(user_id=user.id)
    return stations.Actor(user_id=station_workers.resolve(db, device.outlet_id, station_id, user.id, body.worker_id))


class StationWorkerOut(BaseModel):
    user_id: str
    name: str
    role_name: str | None
    clock_in_at: datetime | None
    # Akun yang login di tablet; pilihan bawaan.
    is_login: bool


# Tidak di-cache: daftar berubah saat karyawan absen masuk atau keluar, dan penulisan tidak pernah membaca dari cache.
@router.get("/station-workers", response_model=list[StationWorkerOut])
def workers(
    station_id: str = Query(min_length=1, max_length=ID_LENGTH),
    device: Device = Depends(tablet),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(stations.PERMISSION_WORK)),
):
    found = station_workers.candidates(db, device.outlet_id, station_id, user.id)
    return [StationWorkerOut(user_id=w.user_id, name=w.name, role_name=w.role_name, clock_in_at=w.clock_in_at, is_login=w.is_login) for w in found]


@router.post("/station-tasks:start", response_model=list[StationBoardOrderOut])
def start(body: StationStepIn, device: Device = Depends(tablet), db: Session = Depends(get_db), user: User = Depends(require_permission(stations.PERMISSION_WORK))):
    try:
        orders = stations.start(db, _worker_of(db, device, user, body), [device.outlet_id], body.task_ids, body.seen)
    except DomainError as error:
        raise _failed(error) from error
    return _stepped(db, orders)


@router.post("/station-tasks:finish", response_model=list[StationBoardOrderOut])
def finish(body: StationStepIn, device: Device = Depends(tablet), db: Session = Depends(get_db), user: User = Depends(require_permission(stations.PERMISSION_WORK))):
    try:
        orders = stations.finish(db, _worker_of(db, device, user, body), [device.outlet_id], body.task_ids, body.seen)
    except DomainError as error:
        raise _failed(error) from error
    return _stepped(db, orders)


class StationPrintIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_ids: list[str] = Field(min_length=1, max_length=stations.MAX_STEP_TASKS)


class StationPrintOut(BaseModel):
    # Menu yang boleh dicetak tablet ini; menu yang sudah dicetak tablet lain tidak ikut.
    task_ids: list[str]


@router.post("/station-tasks:claim-print", response_model=StationPrintOut)
def claim_print(body: StationPrintIn, device: Device = Depends(tablet), db: Session = Depends(get_db), _: User = Depends(require_permission(stations.PERMISSION_WORK))):
    return StationPrintOut(task_ids=stations.claim_print(db, device.outlet_id, body.task_ids))


@router.post("/station-tasks:undo", response_model=list[StationBoardOrderOut])
def undo(body: StationStepIn, device: Device = Depends(tablet), db: Session = Depends(get_db), user: User = Depends(require_permission(stations.PERMISSION_WORK))):
    try:
        orders = stations.undo(db, _worker_of(db, device, user, body), [device.outlet_id], body.task_ids, body.seen)
    except DomainError as error:
        raise _failed(error) from error
    return _stepped(db, orders)


@router.post("/station-tasks:acknowledge", response_model=list[StationBoardOrderOut])
def acknowledge(body: StationAcknowledgeIn, device: Device = Depends(tablet), db: Session = Depends(get_db), user: User = Depends(require_permission(stations.PERMISSION_WORK))):
    try:
        orders = stations.acknowledge(db, stations.Actor(user_id=user.id), [device.outlet_id], body.task_ids)
    except DomainError as error:
        raise _failed(error) from error
    return _stepped(db, orders)


@router.get("/station-recipe", response_model=StationRecipeOut)
def recipe(
    line_ids: str = Query(min_length=1, max_length=MAX_RECIPE_LINES * ID_LENGTH, description="Id baris dipisah koma"),
    device: Device = Depends(tablet),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(stations.PERMISSION_WORK)),
):
    wanted = [part.strip() for part in line_ids.split(",") if part.strip()][:MAX_RECIPE_LINES]
    found = station_recipe.of_lines(db, device.outlet_id, stations.lines_of_branch(db, device.outlet_id, wanted))
    return StationRecipeOut(
        portions=found.portions,
        ingredients=[StationIngredientOut(name=entry.name, unit=entry.unit, per_portion=entry.per_portion, total=entry.total) for entry in found.ingredients],
        without_recipe=found.without_recipe,
    )
