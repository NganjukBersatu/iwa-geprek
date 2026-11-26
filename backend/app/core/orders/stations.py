import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import StrEnum

from sqlalchemy import and_, exists, func, not_, or_, select, tuple_, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from app.core.clock import WIB, as_aware, now
from app.core import page_cursor
from app.core.errors import DomainError
from app.core.finance.sessions import ensure_not_locked
from app.core.orders import reading, stages
from app.core.orders import station_setup as setup_rules
from app.models.cancellation_request import CancellationRequest
from app.models.cash_session import CashSession, CashSessionStatus
from app.models.device import REGISTERED, Device
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.order_item_option import OrderItemOption
from app.models.station import (
    Correction,
    DeviceStation,
    Station,
    StationKind,
    StationMenuStat,
    StationUserStat,
    StationTask,
    StationTaskStep,
    StepKind,
)

log = logging.getLogger("cafe.stations")

PERMISSION_WORK = "order.status"
PERMISSION_INTERVENE = "stasiun.intervensi"
BOARD_LIMIT = 500
MAX_STEP_TASKS = 100
MAX_REASON_LENGTH = 255
MAX_LABEL_LENGTH = 300
NOT_FOUND = 404
CONFLICT = 409

TASK_NOT_FOUND = "Item tidak ditemukan di stasiun ini."
MIXED_STATIONS = "Pilih item dari satu stasiun saja."
MOVED_ELSEWHERE = "Item ini sudah diubah dari perangkat lain. Papan diperbarui."
NOT_ARRIVED = "Item ini belum tiba di stasiun ini."
ORDER_VOIDED = "Pesanan ini sudah dibatalkan."
ITEM_REMOVED = "Item ini sudah dihapus lewat koreksi pesanan."
ALREADY_DELIVERING = "Item ini sudah dibawa pengantar dan tidak bisa dikembalikan dari sini."
NOTHING_TO_ACKNOWLEDGE = "Item ini tidak perlu ditandai."
REASON_REQUIRED = "Isi alasan intervensi."
TOO_MANY = "Pilih paling banyak {limit} item sekali langkah."
# Menu tertinggal lebih lama dari ini ditutup sistem saat kasir membuka sesi, supaya antrean tidak menumpuk sampah.
STALE_BUSINESS_DAYS = 2
STALE_CLOSE_LIMIT = 500
STALE_CLOSE_REASON = "Ditutup otomatis: tertinggal lebih dari 2 hari bisnis"
# Menu di stasiun tanpa tablet tidak punya layar; dihentikan tanpa waktu kerja, per batch STALE_CLOSE_LIMIT dengan paling banyak ORPHAN_STOP_BATCHES putaran.
ORPHAN_STOP_REASON = "Dihentikan sistem: stasiun tidak dipegang perangkat mana pun"
ORPHAN_STOP_BATCHES = 10
LEFT_BEHIND_LIMIT = 100


class Stage(StrEnum):
    WAITING = "waiting"
    STARTED = "started"
    FINISHED = "finished"


def stage_of(task: StationTask) -> Stage:
    if task.finished_at is not None:
        return Stage.FINISHED
    if task.started_at is not None:
        return Stage.STARTED
    return Stage.WAITING


@dataclass(frozen=True)
class Actor:
    user_id: str
    # Terisi hanya saat admin melakukan intervensi dari web.
    reason: str | None = None

    @property
    def intervened(self) -> bool:
        return self.reason is not None


@dataclass(frozen=True)
class BoardTask:
    task: StationTask
    station: Station


@dataclass(frozen=True)
class BoardLine:
    item: OrderItem | None
    options: list[str]
    tasks: list[BoardTask]


@dataclass(frozen=True)
class BoardOrder:
    order: Order
    lines: list[BoardLine]
    pending: CancellationRequest | None
    decided: CancellationRequest | None
    # Sesi kasir pesanan ini sudah ditutup, sedangkan menunya masih di stasiun.
    left_behind: bool
    session_cashier_id: str | None


@dataclass(frozen=True)
class History:
    # Pasangan (tugas, pesanan) terbaru dulu; rincian pesanannya ada di orders.
    entries: list[tuple[str, str]]
    orders: list[BoardOrder]
    next_cursor: str | None


@dataclass(frozen=True)
class Board:
    orders: list[BoardOrder]
    truncated: bool


def prepare_tasks(db: Session, order: Order) -> None:
    # Penjualan tidak boleh gagal karena stasiun; pesanan yang tertinggal tanpa tugas ditemukan Laporan Masalah.
    try:
        with db.begin_nested():
            items = list(db.scalars(select(OrderItem).where(OrderItem.order_id == order.id).order_by(OrderItem.id)).all())
            _add_tasks(db, order, items, setup_rules.setup_of(db, order.outlet_id), None)
            _settle(db, order, now())
    except Exception:
        log.exception("station tasks not prepared", extra={"order_id": order.id})


def _add_tasks(db: Session, order: Order, items: list[OrderItem], setup: setup_rules.BranchSetup, correction: Correction | None) -> None:
    makers = setup_rules.makers_of_menus(db, order.outlet_id, {item.menu_item_id for item in items if item.menu_item_id})
    delivery = setup.delivery_for(order.order_type)
    at = now()
    arrived: list[StationTask] = []
    for item in items:
        maker = setup.maker(makers.get(item.menu_item_id or ""))
        if maker is not None:
            arrived.append(_new_task(db, order, item, maker.station.id, at, correction))
        if delivery is not None:
            # Baris tanpa stasiun pembuat langsung siap diantar.
            task = _new_task(db, order, item, delivery.station.id, at if maker is None else None, correction)
            if maker is None:
                arrived.append(task)
    db.flush()
    for task in arrived:
        db.add(_step(task, StepKind.ARRIVE, None, at))
    db.flush()


def _new_task(db: Session, order: Order, item: OrderItem, station_id: str, arrived: datetime | None, correction: Correction | None) -> StationTask:
    task = StationTask(order_id=order.id, order_item_id=item.id, outlet_id=order.outlet_id, station_id=station_id, arrived_at=arrived, correction=correction)
    db.add(task)
    return task


def _step(task: StationTask, step: StepKind, actor: Actor | None, at: datetime) -> StationTaskStep:
    return StationTaskStep(
        task_id=task.id,
        step=step,
        user_id=actor.user_id if actor else None,
        reason=actor.reason if actor else None,
        intervened=bool(actor and actor.intervened),
        at=at,
    )


def start(db: Session, actor: Actor, outlet_ids: list[str] | None, task_ids: list[str], seen: Stage) -> list[Order]:
    tasks, orders = _lock(db, actor, outlet_ids, task_ids)
    if _already(tasks, Stage.STARTED, seen):
        return orders
    _expect(tasks, Stage.WAITING, seen)
    targets = _targets(db, tasks)
    at = now()
    for task in tasks:
        task.started_at, task.started_by, task.target_seconds = at, actor.user_id, targets.get(task.id)
        db.add(_step(task, StepKind.START, actor, at))
    _commit(db)
    return orders


def finish(db: Session, actor: Actor, outlet_ids: list[str] | None, task_ids: list[str], seen: Stage) -> list[Order]:
    tasks, orders = _lock(db, actor, outlet_ids, task_ids)
    if _already(tasks, Stage.FINISHED, seen):
        return orders
    _expect(tasks, Stage.STARTED, seen)
    station = db.get(Station, tasks[0].station_id)
    at = now()
    for task in tasks:
        task.finished_at, task.finished_by = at, actor.user_id
        db.add(_step(task, StepKind.FINISH, actor, at))
    db.flush()
    if not actor.intervened:
        _count(db, tasks, orders, 1)
    if station is not None and station.kind == StationKind.MAKE:
        _hand_over(db, tasks, actor, at)
    for order in orders:
        _settle(db, order, at)
    _commit(db)
    return orders


def undo(db: Session, actor: Actor, outlet_ids: list[str] | None, task_ids: list[str], seen: Stage) -> list[Order]:
    tasks, orders = _lock(db, actor, outlet_ids, task_ids)
    if seen == Stage.WAITING:
        raise DomainError(MOVED_ELSEWHERE, status=CONFLICT)
    back_to = Stage.STARTED if seen == Stage.FINISHED else Stage.WAITING
    if all(stage_of(task) == back_to for task in tasks):
        return orders
    _expect(tasks, seen, seen)
    station = db.get(Station, tasks[0].station_id)
    at = now()
    if seen == Stage.FINISHED:
        if station is not None and station.kind == StationKind.MAKE:
            _take_back(db, tasks, actor, at)
        _count(db, [task for task in tasks if _counted(db, task)], orders, -1)
    for task in tasks:
        if seen == Stage.FINISHED:
            task.finished_at, task.finished_by = None, None
        else:
            task.started_at, task.started_by, task.target_seconds = None, None, None
        db.add(_step(task, StepKind.UNDO, actor, at))
    db.flush()
    for order in orders:
        _settle(db, order, at)
    _commit(db)
    return orders


def acknowledge(db: Session, actor: Actor, outlet_ids: list[str] | None, task_ids: list[str]) -> list[Order]:
    tasks, orders = _lock(db, actor, outlet_ids, task_ids, acknowledging=True)
    voided = {order.id for order in orders if order.voided_at is not None}
    at = now()
    for task in tasks:
        if task.acknowledged_at is not None:
            continue
        if task.removed_at is None and task.order_id not in voided:
            raise DomainError(NOTHING_TO_ACKNOWLEDGE)
        task.acknowledged_at = at
        db.add(_step(task, StepKind.ACKNOWLEDGE, actor, at))
    _commit(db)
    return orders


def _commit(db: Session) -> None:
    # Versi baris yang sudah berubah berarti tablet lain lebih dulu menyimpan.
    try:
        db.commit()
    except StaleDataError as error:
        db.rollback()
        raise DomainError(MOVED_ELSEWHERE, status=CONFLICT) from error


def _lock(db: Session, actor: Actor, outlet_ids: list[str] | None, task_ids: list[str], acknowledging: bool = False) -> tuple[list[StationTask], list[Order]]:
    ids = sorted(set(task_ids))
    if not ids:
        raise DomainError(TASK_NOT_FOUND, status=NOT_FOUND)
    if len(ids) > MAX_STEP_TASKS:
        raise DomainError(TOO_MANY.format(limit=MAX_STEP_TASKS))
    if actor.reason is not None and not actor.reason.strip():
        raise DomainError(REASON_REQUIRED)
    query = select(StationTask).where(StationTask.id.in_(ids))
    if outlet_ids is not None:
        query = query.where(StationTask.outlet_id.in_(outlet_ids))
    # Dikunci berurutan menurut id supaya dua tablet yang memilih kelompok bertumpuk tidak saling menunggu.
    tasks = list(db.scalars(query.order_by(StationTask.id).with_for_update()).all())
    if len(tasks) != len(ids):
        raise DomainError(TASK_NOT_FOUND, status=NOT_FOUND)
    if len({task.station_id for task in tasks}) > 1:
        raise DomainError(MIXED_STATIONS)
    orders = list(db.scalars(select(Order).where(Order.id.in_({task.order_id for task in tasks})).order_by(Order.id)).all())
    if acknowledging:
        return tasks, orders
    for order in orders:
        if order.voided_at is not None:
            raise DomainError(ORDER_VOIDED, status=CONFLICT)
        ensure_not_locked(db, order)
    for task in tasks:
        if task.removed_at is not None:
            raise DomainError(ITEM_REMOVED, status=CONFLICT)
        if task.arrived_at is None:
            raise DomainError(NOT_ARRIVED, status=CONFLICT)
    return tasks, orders


def _already(tasks: list[StationTask], target: Stage, seen: Stage) -> bool:
    return seen != target and all(stage_of(task) == target for task in tasks)


def _expect(tasks: list[StationTask], expected: Stage, seen: Stage) -> None:
    if seen != expected or any(stage_of(task) != expected for task in tasks):
        raise DomainError(MOVED_ELSEWHERE, status=CONFLICT)


def _targets(db: Session, tasks: list[StationTask]) -> dict[str, int | None]:
    outlet_id = tasks[0].outlet_id
    setup = setup_rules.setup_of(db, outlet_id)
    station = setup.stations.get(tasks[0].station_id)
    if station is None:
        return {}
    if station.station.kind != StationKind.MAKE:
        return {task.id: station.target_seconds for task in tasks}
    menus = dict(db.execute(select(OrderItem.id, OrderItem.menu_item_id).where(OrderItem.id.in_([task.order_item_id for task in tasks if task.order_item_id]))).all())
    targets = setup_rules.menu_targets(db, outlet_id, {menu_id for menu_id in menus.values() if menu_id})
    return {task.id: targets.get(menus.get(task.order_item_id or "") or "") for task in tasks}


def _counted(db: Session, task: StationTask) -> bool:
    # Hanya selesai yang ditekan karyawan sendiri yang masuk ringkasan, jadi pembatalannya pun hanya mengurangi yang itu.
    last = db.scalar(
        select(StationTaskStep.intervened)
        .where(StationTaskStep.task_id == task.id, StationTaskStep.step == StepKind.FINISH)
        .order_by(StationTaskStep.at.desc(), StationTaskStep.id.desc())
        .limit(1)
    )
    return last is False


def _count(db: Session, tasks: list[StationTask], orders: list[Order], sign: int) -> None:
    if not tasks:
        return
    by_order = {order.id: order for order in orders}
    lines = {item.id: item for item in db.scalars(select(OrderItem).where(OrderItem.id.in_([task.order_item_id for task in tasks if task.order_item_id]))).all()}
    for task in tasks:
        order = by_order.get(task.order_id)
        if order is None or task.arrived_at is None or task.started_at is None or task.finished_at is None:
            continue
        wait = int((as_aware(task.started_at) - as_aware(task.arrived_at)).total_seconds())
        work = int((as_aware(task.finished_at) - as_aware(task.started_at)).total_seconds())
        targeted = task.target_seconds is not None
        figures = {
            "tasks": sign,
            "wait_seconds": sign * wait,
            "work_seconds": sign * work,
            "targeted": sign * int(targeted),
            "on_time": sign * int(targeted and work <= (task.target_seconds or 0)),
        }
        key = {"outlet_id": task.outlet_id, "business_day": order.business_day, "hour": as_aware(order.created_at).astimezone(WIB).hour, "station_id": task.station_id}
        _add_stat(db, StationUserStat, {**key, "user_id": task.started_by}, ["outlet_id", "business_day", "hour", "station_id", "user_id"], figures)
        line = lines.get(task.order_item_id or "")
        if line is not None and line.menu_item_id:
            _add_stat(
                db,
                StationMenuStat,
                {**key, "menu_item_id": line.menu_item_id, "menu_name": line.menu_item_name[:255]},
                ["outlet_id", "business_day", "hour", "station_id", "menu_item_id"],
                figures,
            )


def _add_stat(db: Session, model, key: dict, conflict: list[str], figures: dict[str, int]) -> None:
    statement = insert(model).values(**key, **figures)
    statement = statement.on_conflict_do_update(index_elements=conflict, set_={name: getattr(model, name) + statement.excluded[name] for name in figures})
    db.execute(statement.execution_options(live_silent=True))


def _delivery_tasks(db: Session, item_ids: list[str]) -> list[StationTask]:
    if not item_ids:
        return []
    return list(
        db.scalars(
            select(StationTask)
            .join(Station, Station.id == StationTask.station_id)
            .where(StationTask.order_item_id.in_(item_ids), Station.kind != StationKind.MAKE)
            .order_by(StationTask.id)
            .with_for_update(of=StationTask)
        ).all()
    )


def _hand_over(db: Session, made: list[StationTask], actor: Actor, at: datetime) -> None:
    for task in _delivery_tasks(db, [task.order_item_id for task in made if task.order_item_id]):
        if task.arrived_at is None and task.removed_at is None:
            task.arrived_at = at
            db.add(_step(task, StepKind.ARRIVE, actor, at))


def _take_back(db: Session, made: list[StationTask], actor: Actor, at: datetime) -> None:
    delivering = _delivery_tasks(db, [task.order_item_id for task in made if task.order_item_id])
    if any(task.started_at is not None for task in delivering):
        raise DomainError(ALREADY_DELIVERING, status=CONFLICT)
    for task in delivering:
        if task.arrived_at is not None:
            task.arrived_at = None
            db.add(_step(task, StepKind.UNDO, actor, at))


def _settle(db: Session, order: Order, at: datetime) -> None:
    # Pesanan selesai saat setiap baris yang tersisa selesai di stasiun terakhirnya, dan terbuka lagi saat satu dikembalikan.
    served = _served(db, order)
    if served and order.served_at is None:
        final = next((stage[stages.CODE] for stage in stages.of_branch(db, order.outlet_id) if stage.get(stages.LAST)), None)
        if final is not None:
            order.serving_status = final
        order.served_at = at
    elif not served and order.served_at is not None:
        order.serving_status = stages.first_code(db, order.outlet_id)
        order.served_at = None


def _served(db: Session, order: Order) -> bool:
    rows = db.execute(
        select(StationTask.order_item_id, StationTask.id, Station.kind, StationTask.finished_at)
        .join(Station, Station.id == StationTask.station_id)
        .where(StationTask.order_id == order.id, StationTask.removed_at.is_(None))
    ).all()
    # Tanpa stasiun yang dipakai, checkpoint terakhirnya Kasir, yang terpenuhi saat pesanan dibayar.
    if not rows:
        return True
    last: dict[str, tuple[str, datetime | None]] = {}
    for item_id, task_id, kind, finished_at in rows:
        key = item_id or task_id
        current = last.get(key)
        # Tugas pengantar adalah langkah terakhir sebuah baris; tugas pembuat hanya bila baris itu tidak diantar.
        if current is None or current[0] == StationKind.MAKE:
            last[key] = (kind, finished_at)
    return all(finished_at is not None for _, finished_at in last.values())


@dataclass
class LinesBefore:
    keyed: dict[tuple, list[tuple[OrderItem, list[StationTask]]]] = field(default_factory=dict)


def _line_key(item: OrderItem, options: list[OrderItemOption]) -> tuple:
    chosen = tuple(sorted((option.kind, option.ref_id or option.name, option.qty) for option in options))
    return (item.menu_item_id or item.menu_item_name, chosen, (item.note or "").strip())


def lines_before_edit(db: Session, order: Order) -> LinesBefore:
    # Dibaca sebelum baris dihapus koreksi; tugasnya bertahan dengan baris kosong berkat SET NULL.
    before = LinesBefore()
    items = list(db.scalars(select(OrderItem).where(OrderItem.order_id == order.id).order_by(OrderItem.id)).all())
    if not items:
        return before
    options = _options_of(db, [item.id for item in items])
    tasks: dict[str, list[StationTask]] = defaultdict(list)
    for task in db.scalars(select(StationTask).where(StationTask.order_id == order.id, StationTask.removed_at.is_(None)).order_by(StationTask.id)).all():
        if task.order_item_id:
            tasks[task.order_item_id].append(task)
    for item in items:
        before.keyed.setdefault(_line_key(item, options.get(item.id, [])), []).append((item, tasks.get(item.id, [])))
    return before


def sync_after_edit(db: Session, order: Order, before: LinesBefore | None) -> None:
    at = now()
    setup = setup_rules.setup_of(db, order.outlet_id)
    if before is not None:
        items = list(db.scalars(select(OrderItem).where(OrderItem.order_id == order.id).order_by(OrderItem.id)).all())
        options = _options_of(db, [item.id for item in items])
        added: list[OrderItem] = []
        for item in items:
            matches = before.keyed.get(_line_key(item, options.get(item.id, [])))
            if not matches:
                added.append(item)
                continue
            old, tasks = matches.pop(0)
            for task in tasks:
                task.order_item_id = item.id
                if old.qty != item.qty:
                    task.correction = Correction.CHANGED
        for matches in before.keyed.values():
            for old, tasks in matches:
                for task in tasks:
                    task.order_item_id = None
                    task.removed_at, task.removed_label = at, f"{old.qty}x {old.menu_item_name}"[:MAX_LABEL_LENGTH]
                    # Stasiun yang belum menerima baris itu tidak punya apa pun untuk dihentikan.
                    if task.arrived_at is None:
                        task.acknowledged_at = at
        if added and order.voided_at is None:
            _add_tasks(db, order, added, setup, Correction.ADDED)
    _reroute_delivery(db, order, setup)
    db.flush()
    _settle(db, order, at)


def _reroute_delivery(db: Session, order: Order, setup: setup_rules.BranchSetup) -> None:
    # Jenis pesanan yang diubah memindahkan baris yang belum dibawa ke stasiun yang kini mengantarnya.
    target = setup.delivery_for(order.order_type)
    if target is None:
        return
    for task in db.scalars(
        select(StationTask)
        .join(Station, Station.id == StationTask.station_id)
        .where(
            StationTask.order_id == order.id,
            Station.kind != StationKind.MAKE,
            StationTask.station_id != target.station.id,
            StationTask.started_at.is_(None),
            StationTask.removed_at.is_(None),
        )
        .order_by(StationTask.id)
    ).all():
        task.station_id = target.station.id


def _options_of(db: Session, item_ids: list[str]) -> dict[str, list[OrderItemOption]]:
    found: dict[str, list[OrderItemOption]] = defaultdict(list)
    if item_ids:
        for option in db.scalars(select(OrderItemOption).where(OrderItemOption.order_item_id.in_(item_ids)).order_by(OrderItemOption.id)).all():
            found[option.order_item_id].append(option)
    return found


def board(db: Session, outlet_id: str) -> Board:
    # Antrean mengikuti keadaan menu, bukan sesi kasir: menu tetap tampil sampai selesai walau sesi kasirnya sudah ditutup.
    unfinished = _open_tasks(outlet_id)
    # Pesanan batal tetap tampil sampai setiap stasiun yang sedang memegangnya menekan Mengerti.
    unacknowledged = exists().where(
        StationTask.order_id == Order.id, StationTask.acknowledged_at.is_(None), StationTask.arrived_at.is_not(None), StationTask.finished_at.is_(None)
    )
    rows = list(
        db.scalars(
            select(Order)
            .where(
                Order.outlet_id == outlet_id,
                Order.id.in_(unfinished),
                Order.served_at.is_(None),
                or_(Order.voided_at.is_(None), unacknowledged),
            )
            .order_by(Order.created_at, Order.id)
            .limit(BOARD_LIMIT + 1)
        ).all()
    )
    return Board(orders=board_of(db, rows[:BOARD_LIMIT]), truncated=len(rows) > BOARD_LIMIT)


def board_of(db: Session, orders: list[Order]) -> list[BoardOrder]:
    if not orders:
        return []
    order_ids = [order.id for order in orders]
    lines = {entry.order.id: entry for entry in reading.lines_of(db, orders)}
    tasks = list(db.scalars(select(StationTask).where(StationTask.order_id.in_(order_ids)).order_by(StationTask.id)).all())
    stations = {station.id: station for station in db.scalars(select(Station).where(Station.id.in_({task.station_id for task in tasks}))).all()} if tasks else {}
    pending, decided = _requests(db, order_ids)
    session_ids = {order.cash_session_id for order in orders if order.cash_session_id}
    sessions = {
        row.id: row
        for row in db.execute(select(CashSession.id, CashSession.status, CashSession.cashier_id).where(CashSession.id.in_(session_ids))).all()
    } if session_ids else {}

    by_item: dict[str, list[StationTask]] = defaultdict(list)
    removed: dict[str, list[StationTask]] = defaultdict(list)
    for task in tasks:
        if task.order_item_id:
            by_item[task.order_item_id].append(task)
        elif task.acknowledged_at is None:
            removed[task.order_id].append(task)

    def shaped(task_list: list[StationTask]) -> list[BoardTask]:
        result = [
            BoardTask(task, stations[task.station_id])
            for task in task_list
            if task.station_id in stations
        ]
        result.sort(key=lambda entry: (entry.station.kind != StationKind.MAKE, entry.station.position, entry.station.name))
        return result

    result = []
    for order in orders:
        entry = lines.get(order.id)
        board_lines = [BoardLine(item, [option.name for option in entry.options.get(item.id, [])], shaped(by_item.get(item.id, []))) for item in (entry.items if entry else [])]
        board_lines += [BoardLine(None, [], shaped([task])) for task in removed.get(order.id, [])]
        session = sessions.get(order.cash_session_id or "")
        left_behind = session is not None and session.status != CashSessionStatus.OPEN and order.served_at is None
        result.append(BoardOrder(order, board_lines, pending.get(order.id), decided.get(order.id), left_behind, session.cashier_id if session else None))
    return result


def _history_since(db: Session, outlet_id: str) -> datetime | None:
    # Riwayat mencakup sesi kasir yang masih terbuka di cabang; bila tidak ada, sesi terakhir yang ditutup.
    opened = db.scalar(select(func.min(CashSession.opened_at)).where(CashSession.outlet_id == outlet_id, CashSession.status == CashSessionStatus.OPEN))
    if opened is not None:
        return opened
    return db.scalar(
        select(CashSession.opened_at)
        .where(CashSession.outlet_id == outlet_id, CashSession.status != CashSessionStatus.OPEN)
        .order_by(CashSession.opened_at.desc(), CashSession.id.desc())
        .limit(1)
    )


class HistoryPart(StrEnum):
    """Pembagian menu yang sudah selesai di stasiun: pesanannya masih berjalan, atau sudah tuntas atau dibatalkan."""

    MOVING = "moving"
    DONE = "done"


def history(db: Session, outlet_id: str, station_id: str, cursor: str | None, limit: int, part: HistoryPart | None = None) -> History:
    """Menu yang sudah selesai di satu stasiun, terbaru dulu dan berkursor; dibatasi waktu lewat indeks (outlet_id, finished_at)."""
    since = _history_since(db, outlet_id)
    if since is None:
        return History(entries=[], orders=[], next_cursor=None)
    scope = f"station-history\0{outlet_id}\0{station_id}\0{since.isoformat()}\0{part or ''}"
    statement = select(StationTask.id, StationTask.order_id, StationTask.finished_at).where(
        StationTask.outlet_id == outlet_id,
        StationTask.station_id == station_id,
        StationTask.finished_at >= since,
        StationTask.removed_at.is_(None),
    )
    if part is not None:
        # Tuntas dibaca dari selesai_at pesanan yang diisi saat semua langkahnya selesai, sama dengan yang dipakai papan.
        moving = and_(Order.served_at.is_(None), Order.voided_at.is_(None))
        statement = statement.join(Order, Order.id == StationTask.order_id).where(moving if part == HistoryPart.MOVING else not_(moving))
    if cursor:
        after = page_cursor.decode(scope, cursor)
        statement = statement.where(tuple_(StationTask.finished_at, StationTask.id) < tuple_(after.at, after.id))
    found = db.execute(statement.order_by(StationTask.finished_at.desc(), StationTask.id.desc()).limit(limit + 1)).all()
    rows = found[:limit]
    next_cursor = None
    if len(found) > limit:
        last = rows[-1]
        next_cursor = page_cursor.encode(scope, page_cursor.Position(at=as_aware(last.finished_at), id=last.id))
    order_ids = list(dict.fromkeys(row.order_id for row in rows))
    orders = list(db.scalars(select(Order).where(Order.id.in_(order_ids)).order_by(Order.id)).all()) if order_ids else []
    return History(entries=[(row.id, row.order_id) for row in rows], orders=board_of(db, orders), next_cursor=next_cursor)


def _open_tasks(outlet_id: str):
    # Predikat sama persis dengan indeks parsial index_station_tasks_on_outlet_id_open, supaya tugas yang sudah selesai atau dimengerti tidak ikut dipindai.
    return select(StationTask.order_id).where(StationTask.outlet_id == outlet_id, StationTask.finished_at.is_(None), StationTask.acknowledged_at.is_(None))


def left_behind_orders(db: Session, outlet_id: str) -> list[Order]:
    """Pesanan cabang dari sesi kasir yang sudah ditutup yang menunya masih di stasiun, terlama dulu."""
    unfinished = _open_tasks(outlet_id).where(StationTask.removed_at.is_(None))
    return list(
        db.scalars(
            select(Order)
            .join(CashSession, CashSession.id == Order.cash_session_id)
            .where(
                Order.outlet_id == outlet_id,
                Order.id.in_(unfinished),
                Order.served_at.is_(None),
                Order.voided_at.is_(None),
                CashSession.status != CashSessionStatus.OPEN,
            )
            .order_by(Order.created_at, Order.id)
            .limit(LEFT_BEHIND_LIMIT)
        ).all()
    )


def close_stale(db: Session, outlet_id: str, day: date) -> int:
    """Menutup menu tertinggal dari pesanan lebih tua dari STALE_BUSINESS_DAYS hari bisnis sebagai intervensi sistem, jadi tidak masuk Kinerja; menu batal atau dihapus cukup dimengerti."""
    oldest = day - timedelta(days=STALE_BUSINESS_DAYS)
    tasks = list(
        db.scalars(
            select(StationTask)
            .join(Order, Order.id == StationTask.order_id)
            .join(CashSession, CashSession.id == Order.cash_session_id)
            .where(
                StationTask.outlet_id == outlet_id,
                StationTask.finished_at.is_(None),
                StationTask.acknowledged_at.is_(None),
                Order.business_day < oldest,
                CashSession.status != CashSessionStatus.OPEN,
            )
            .order_by(StationTask.id)
            .limit(STALE_CLOSE_LIMIT)
            .with_for_update(of=StationTask, skip_locked=True)
        ).all()
    )
    if not tasks:
        return 0
    at = now()
    voided = set(db.scalars(select(Order.id).where(Order.id.in_({task.order_id for task in tasks}), Order.voided_at.is_not(None))).all())
    for task in tasks:
        if task.removed_at is not None or task.order_id in voided:
            task.acknowledged_at = at
            db.add(_system_step(task, StepKind.ACKNOWLEDGE, at))
            continue
        if task.arrived_at is None:
            task.arrived_at = at
            db.add(_system_step(task, StepKind.ARRIVE, at))
        if task.started_at is None:
            task.started_at = at
            db.add(_system_step(task, StepKind.START, at))
        task.finished_at = at
        db.add(_system_step(task, StepKind.FINISH, at))
    db.flush()
    for order in db.scalars(select(Order).where(Order.id.in_({task.order_id for task in tasks})).order_by(Order.id)).all():
        if order.voided_at is None:
            _settle(db, order, at)
    _commit(db)
    return len(tasks)


def stop_orphans(db: Session, outlet_id: str) -> int:
    """Menghentikan menu yang menunggu di stasiun yang tidak dipegang tablet terdaftar mana pun di cabang ini, tanpa waktu kerja dan di luar Kinerja.

    Menu itu tidak punya layar sehingga tidak bisa diselesaikan siapa pun; hanya removed_at, acknowledged_at, dan satu langkah sistem yang diisi,
    jadi tidak ada durasi atau keterlambatan. Dipanggil dalam transaksi pemanggil, yang melakukan commit.
    """
    held = exists().where(
        DeviceStation.station_id == StationTask.station_id,
        DeviceStation.device_id == Device.id,
        Device.outlet_id == outlet_id,
        Device.status == REGISTERED,
    )
    stopped = 0
    for _ in range(ORPHAN_STOP_BATCHES):
        # Predikat terbuka sama dengan indeks parsial index_station_tasks_on_outlet_id_open.
        tasks = list(
            db.scalars(
                select(StationTask)
                .where(StationTask.outlet_id == outlet_id, StationTask.finished_at.is_(None), StationTask.acknowledged_at.is_(None), not_(held))
                .order_by(StationTask.id)
                .limit(STALE_CLOSE_LIMIT)
                .with_for_update(of=StationTask, skip_locked=True)
            ).all()
        )
        if not tasks:
            break
        at = now()
        item_ids = [task.order_item_id for task in tasks if task.order_item_id and task.removed_at is None]
        labels = (
            {item.id: f"{item.qty}x {item.menu_item_name}"[:MAX_LABEL_LENGTH] for item in db.scalars(select(OrderItem).where(OrderItem.id.in_(item_ids))).all()} if item_ids else {}
        )
        for task in tasks:
            if task.removed_at is None:
                task.removed_at = at
                task.removed_label = labels.get(task.order_item_id or "") or task.removed_label
            task.acknowledged_at = at
            db.add(_system_step(task, StepKind.ACKNOWLEDGE, at, ORPHAN_STOP_REASON))
        db.flush()
        voided = set(db.scalars(select(Order.id).where(Order.id.in_({task.order_id for task in tasks}), Order.voided_at.is_not(None))).all())
        for order in db.scalars(select(Order).where(Order.id.in_({task.order_id for task in tasks} - voided)).order_by(Order.id)).all():
            _settle(db, order, at)
        stopped += len(tasks)
    return stopped


def _system_step(task: StationTask, step: StepKind, at: datetime, reason: str = STALE_CLOSE_REASON) -> StationTaskStep:
    # Langkah sistem tanpa karyawan; finished_by kosong menandai Ditutup sistem.
    return StationTaskStep(task_id=task.id, step=step, user_id=None, reason=reason, intervened=True, at=at)


def _requests(db: Session, order_ids: list[str]) -> tuple[dict[str, CancellationRequest], dict[str, CancellationRequest]]:
    pending: dict[str, CancellationRequest] = {}
    decided: dict[str, CancellationRequest] = {}
    for row in db.scalars(select(CancellationRequest).where(CancellationRequest.order_id.in_(order_ids)).order_by(CancellationRequest.created_at, CancellationRequest.id)).all():
        if row.decided_at is None:
            pending[row.order_id] = row
        else:
            decided[row.order_id] = row
    return pending, decided


def claim_print(db: Session, outlet_id: str, task_ids: list[str]) -> list[str]:
    """Menandai struk pesanan menu yang sudah selesai sebagai tercetak; hanya yang belum pernah ditandai yang dikembalikan, jadi satu tablet saja yang mencetak."""
    wanted = sorted(set(task_ids))[:MAX_STEP_TASKS]
    if not wanted:
        return []
    claimed = db.scalars(
        update(StationTask)
        .where(
            StationTask.id.in_(wanted),
            StationTask.outlet_id == outlet_id,
            StationTask.finished_at.is_not(None),
            StationTask.removed_at.is_(None),
            StationTask.printed_at.is_(None),
        )
        .values(printed_at=now())
        .returning(StationTask.id)
        .execution_options(synchronize_session=False)
    ).all()
    db.commit()
    return list(claimed)


def lines_of_branch(db: Session, outlet_id: str, item_ids: list[str]) -> list[str]:
    if not item_ids:
        return []
    return list(db.scalars(select(OrderItem.id).join(Order, Order.id == OrderItem.order_id).where(OrderItem.id.in_(item_ids), Order.outlet_id == outlet_id)).all())


def open_count(db: Session, session_id: str) -> int:
    return int(
        db.scalar(
            select(func.count())
            .select_from(Order)
            .where(Order.cash_session_id == session_id, Order.voided_at.is_(None), Order.served_at.is_(None), exists().where(StationTask.order_id == Order.id))
        )
        or 0
    )
