"""Data demo Papan Stasiun: stasiun Bar, Dapur, Waiters, dan Kasir, alurnya di cabang pertama, lalu beberapa pesanan terbuka dalam berbagai tahap.

    python scripts/seed_demo_stations.py           # menampilkan rencana dan menulis tidak apa pun
    python scripts/seed_demo_stations.py --tulis   # menulis data demo setelah Anda mengetik "ya"
    python scripts/seed_demo_stations.py --hapus   # menghapus semua data demo stasiun setelah Anda mengetik "ya"

Hanya untuk database pengembangan; database tujuannya (DATABASE_URL) ditampilkan sebelum menulis.
Butuh data dari scripts/seed_demo_sales.py (kategori, menu, dan kasir demo) di cabang pertama.
Semua barisnya berawalan "demo-st" supaya bisa dihapus lagi tanpa menyentuh data demo penjualan.
"""
import sys
import uuid
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import delete, func, select, update  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402
from sqlalchemy.exc import ProgrammingError  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.clock import now  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.core.orders import stages, stations  # noqa: E402
from app.core.orders.order_types import DINE_IN, TAKE_AWAY  # noqa: E402
from app.core.settings import settings  # noqa: E402
from app.models.cancellation_request import CancellationRequest, CancellationStatus  # noqa: E402
from app.models.cash_session import CashSession, CashSessionStatus  # noqa: E402
from app.models.category import Category  # noqa: E402
from app.models.menu_item import MenuItem  # noqa: E402
from app.models.order import Order  # noqa: E402
from app.models.order_item import OrderItem  # noqa: E402
from app.models.outlet import Outlet  # noqa: E402
from app.models.payment_method import PaymentMethod  # noqa: E402
from app.models.user import User  # noqa: E402
from scripts import demo_catalog  # noqa: E402
from app.models.station import (  # noqa: E402
    CategoryStation,
    MenuTarget,
    Station,
    StationBranchSetting,
    StationFlow,
    StationMenuStat,
    StationUserStat,
    StationTask,
    StationTaskStep,
)

PREFIX = "demo-st"
CONFIRMATION = "ya"
MAKE_TARGET_SECONDS = 240
DELIVER_TARGET_SECONDS = 180
HANDOVER_TARGET_SECONDS = 60
BAR_ID = f"{PREFIX}-station-bar"
KITCHEN_ID = f"{PREFIX}-station-kitchen"
WAITERS_ID = f"{PREFIX}-station-waiters"
CASHIER_ID = f"{PREFIX}-station-cashier"
SESSION_ID = f"{PREFIX}-session"
STATIONS = (
    (BAR_ID, "Bar", "make", 10, None),
    (KITCHEN_ID, "Dapur", "make", 11, None),
    (WAITERS_ID, "Waiters", "deliver", 12, DELIVER_TARGET_SECONDS),
    (CASHIER_ID, "Kasir", "handover", 13, HANDOVER_TARGET_SECONDS),
)
# Kategori demo penjualan diarahkan ke stasiun pembuatnya.
# Kategori menu dan stasiun pembuatnya dari demo_catalog.json milik klien.
CATEGORY_STATIONS = {category.name: BAR_ID if category.station == "bar" else KITCHEN_ID for category in demo_catalog.load().menu_categories}


# (jenis, meja, [(stasiun pembuat, jumlah)], menit sejak dibuat); menunya diambil bergiliran dari kategori katalog klien di stasiun itu.
ORDER_SHAPES = (
    (DINE_IN, "4", (("bar", 2), ("kitchen", 1)), 9),
    (TAKE_AWAY, None, (("bar", 1), ("bar", 1)), 2),
    (DINE_IN, "7", (("bar", 2), ("kitchen", 1)), 1),
    (DINE_IN, "2", (("bar", 1),), 3),
    (DINE_IN, "9", (("bar", 1), ("kitchen", 1)), 6),
    (DINE_IN, "5", (("kitchen", 1),), 5),
    (DINE_IN, "1", (("bar", 1),), 12),
    (TAKE_AWAY, None, (("kitchen", 1),), 8),
)


def order_plan(catalog: demo_catalog.Catalog) -> list[tuple[str, str | None, list[tuple[str, int]], int]]:
    """Pesanan antrean papan stasiun dengan menu klien sendiri; stasiun tanpa kategori memakai menu stasiun lainnya."""
    by_station: dict[str, list[str]] = {}
    for category in catalog.menu_categories:
        by_station.setdefault(category.station, []).extend(menu.name for menu in category.menus)
    every = [menu.name for menu in catalog.menus()]
    turns: dict[str, int] = {}
    plan = []
    for order_type, table, lines, minutes in ORDER_SHAPES:
        chosen = []
        for station, qty in lines:
            names = by_station.get(station) or every
            turn = turns.get(station, 0)
            chosen.append((names[turn % len(names)], qty))
            turns[station] = turn + 1
        plan.append((order_type, table, chosen, minutes))
    return plan


def new_id() -> str:
    return f"{PREFIX}-{uuid.uuid4()}"


def delete_demo(db: Session) -> None:
    order_ids = select(Order.id).where(Order.id.like(f"{PREFIX}-%"))
    task_ids = select(StationTask.id).where(StationTask.order_id.in_(order_ids))
    db.execute(delete(StationTaskStep).where(StationTaskStep.task_id.in_(task_ids)))
    db.execute(delete(StationTask).where(StationTask.order_id.in_(order_ids)))
    db.execute(delete(CancellationRequest).where(CancellationRequest.order_id.in_(order_ids)))
    db.execute(delete(OrderItem).where(OrderItem.order_id.in_(order_ids)))
    db.execute(delete(Order).where(Order.id.like(f"{PREFIX}-%")))
    db.execute(delete(CashSession).where(CashSession.id == SESSION_ID))
    db.execute(delete(StationUserStat).where(StationUserStat.station_id.like(f"{PREFIX}-%")))
    db.execute(delete(StationMenuStat).where(StationMenuStat.station_id.like(f"{PREFIX}-%")))
    db.execute(delete(StationBranchSetting).where(StationBranchSetting.station_id.like(f"{PREFIX}-%")))
    db.execute(delete(CategoryStation).where(CategoryStation.station_id.like(f"{PREFIX}-%")))
    db.execute(delete(MenuTarget).where(MenuTarget.menu_item_id.like("demo-%"), MenuTarget.target_seconds == MAKE_TARGET_SECONDS))
    db.execute(delete(Station).where(Station.id.like(f"{PREFIX}-%")))
    remaining = db.scalar(select(func.count()).select_from(StationBranchSetting).where(StationBranchSetting.used)) or 0
    if remaining == 0:
        db.execute(delete(StationFlow))
    db.commit()


def age(db: Session, task_id: str, arrived: int | None = None, started: int | None = None) -> None:
    """Menggeser waktu tugas ke belakang (dalam menit) supaya pewaktu di layar menunjukkan keadaan yang berbeda-beda."""
    task = db.get(StationTask, task_id)
    stamp = now()
    if arrived is not None:
        task.arrived_at = stamp - timedelta(minutes=arrived)
    if started is not None and task.started_at is not None:
        task.started_at = stamp - timedelta(minutes=started)
    db.commit()


def tasks_at(db: Session, order_id: str, station_id: str) -> list[StationTask]:
    return list(db.scalars(select(StationTask).where(StationTask.order_id == order_id, StationTask.station_id == station_id).order_by(StationTask.id)).all())


def main() -> int:
    mode = "--tulis" if "--tulis" in sys.argv[1:] else "--hapus" if "--hapus" in sys.argv[1:] else None
    url = make_url(settings.database_url)
    target = f"{url.host}:{url.port}/{url.database}"
    print(f"Database: {target}")
    with SessionLocal() as db:
        try:
            # Cabang yang memiliki menu demo penjualan, supaya tablet di cabang itu melihat kategori dan menunya.
            demo_menu = db.scalars(select(MenuItem).where(MenuItem.id.like("demo-%")).limit(1)).first()
            outlet = db.get(Outlet, demo_menu.outlet_ids[0]) if demo_menu is not None and demo_menu.outlet_ids else db.scalars(select(Outlet).order_by(Outlet.name, Outlet.id).limit(1)).first()
        except ProgrammingError:
            db.rollback()
            print("Tabel belum ada di database ini. Jalankan dulu: python -m alembic upgrade head. Tidak ada yang diubah.")
            return 1
        if outlet is None:
            print("Belum ada cabang. Jalankan scripts/create_owner.py lebih dulu. Tidak ada yang diubah.")
            return 1
        existing = db.scalar(select(func.count()).select_from(Station).where(Station.id.like(f"{PREFIX}-%"))) or 0

        if mode == "--hapus":
            print(f"Akan menghapus data demo stasiun ({existing} stasiun beserta pesanan, tugas, dan sesi demonya).")
            if input(f'Ketik "{CONFIRMATION}" untuk melanjutkan: ').strip().lower() != CONFIRMATION:
                print("Dibatalkan. Tidak ada yang dihapus.")
                return 1
            delete_demo(db)
            print("Selesai. Data demo stasiun dihapus.")
            return 0

        print(f"Cabang: {outlet.name}")
        print("Rencana: stasiun Bar, Dapur, Waiters, dan Kasir; alur stasiun aktif; kategori demo diarahkan ke Bar atau Dapur; satu sesi kasir demo yang terbuka;")
        print("delapan pesanan terbuka: menunggu, diproses, terlambat, menunggu diantar, pengajuan pembatalan, dan pesanan yang dibatalkan.")
        if existing:
            print("Data demo stasiun sudah ada. Jalankan dengan --hapus dulu bila ingin membuatnya ulang. Tidak ada yang diubah.")
            return 0
        if mode != "--tulis":
            print("Belum ada yang ditulis. Jalankan dengan --tulis untuk membuatnya.")
            return 0

        cashiers = list(db.scalars(select(User).where(User.username.like("demo.kasir%")).order_by(User.username)).all())
        categories = {c.name: c for c in db.scalars(select(Category).where(Category.name.in_(list(CATEGORY_STATIONS)))).all()}
        menu = {m.name: m for m in db.scalars(select(MenuItem).where(MenuItem.id.like("demo-%"))).all()}
        method = db.scalars(select(PaymentMethod).where(PaymentMethod.outlet_id == outlet.id, PaymentMethod.code == "tunai")).first()
        if len(cashiers) < 2 or len(categories) < len(CATEGORY_STATIONS) or not menu or method is None:
            print("Data demo penjualan belum lengkap. Jalankan dulu: python scripts/seed_demo_sales.py --tulis. Tidak ada yang diubah.")
            return 1
        if input(f'Akan menulis ke database {target}. Ketik "{CONFIRMATION}" untuk melanjutkan: ').strip().lower() != CONFIRMATION:
            print("Dibatalkan. Tidak ada yang ditulis.")
            return 1

        counter, worker = cashiers[0], cashiers[1]
        stamp = now()
        # Migrasi sudah membuat stasiun Kasir, dan jenis Kasir hanya boleh satu, jadi demo memakai yang ada.
        cashier_station = db.scalar(select(Station.id).where(Station.kind == "handover"))
        for station_id, name, kind, position, target_seconds in STATIONS:
            if kind == "handover" and cashier_station is not None:
                station_id = cashier_station
            else:
                db.add(Station(id=station_id, name=name, kind=kind, position=position, target_seconds=target_seconds))
            db.add(StationBranchSetting(outlet_id=outlet.id, station_id=station_id, used=True, target_seconds=None))
        # Stasiun harus sudah tersimpan sebelum kategori dan pengaturan cabang merujuknya; model di proyek ini tidak menyatakan relasi, jadi urutan tulis tidak dihitung otomatis.
        db.flush()
        db.merge(StationFlow(outlet_id=outlet.id, active=True))
        for category_name, station_id in CATEGORY_STATIONS.items():
            db.merge(CategoryStation(category_id=categories[category_name].id, station_id=station_id))
        for item in menu.values():
            if db.get(MenuTarget, item.id) is None:
                db.add(MenuTarget(menu_item_id=item.id, target_seconds=MAKE_TARGET_SECONDS))
        session = db.get(CashSession, SESSION_ID)
        if session is None:
            session = CashSession(
                id=SESSION_ID,
                outlet_id=outlet.id,
                cashier_id=counter.id,
                shift_code_id=None,
                shift_code=None,
                shift_code_color=None,
                opened_at=stamp - timedelta(hours=2),
                closed_at=None,
                opening_cash=Decimal("500000"),
                system_revenue=Decimal("0"),
                cash_revenue=Decimal("0"),
                drawer_expenses=Decimal("0"),
                status=CashSessionStatus.OPEN,
            )
            db.add(session)
        db.flush()

        plan = order_plan(demo_catalog.load())
        orders: list[Order] = []
        for index, (order_type, table, lines, minutes) in enumerate(plan, start=1):
            created = stamp - timedelta(minutes=minutes)
            total = Decimal("0")
            order_id = new_id()
            items = []
            for name, qty in lines:
                found = menu[name]
                total += found.price * qty
                items.append(
                    OrderItem(id=new_id(), order_id=order_id, menu_item_id=found.id, menu_item_name=found.name, unit_price=found.price, unit_cost=(found.price * Decimal("0.35")).quantize(Decimal("1")), qty=qty, subtotal=found.price * qty, note=None)
                )
            order = Order(
                id=order_id,
                cash_session_id=session.id,
                outlet_id=outlet.id,
                cashier_id=counter.id,
                customer_name=None,
                table_no=table,
                order_type=order_type,
                visitor_category_id=None,
                visitor_category_label=None,
                visitor_gender_id=None,
                visitor_gender_label=None,
                note_id=None,
                note_label=None,
                receipt_number=f"DEMO-ST-{index:03d}",
                client_id=None,
                payment_method=method.code,
                payment_method_label=method.label,
                payment_method_id=method.id,
                cash_received=total,
                promo_id=None,
                discount=Decimal("0"),
                total=total,
                created_at=created,
                voided_at=None,
                void_reason=None,
                voided_by_id=None,
                serving_status=stages.first_code(db, outlet.id),
                served_at=None,
            )
            db.add(order)
            db.add_all(items)
            orders.append(order)
        db.flush()
        for order in orders:
            stations.prepare_tasks(db, order)
        db.commit()

        actor = stations.Actor(user_id=worker.id)
        waiting = stations.Stage.WAITING
        started = stations.Stage.STARTED

        def ids(order: Order, station_id: str) -> list[str]:
            return [task.id for task in tasks_at(db, order.id, station_id)]

        # Klien yang semua menunya di satu stasiun tidak punya tugas di stasiun lain; langkah untuk stasiun itu dilewati.
        def start(task_ids: list[str]) -> None:
            if task_ids:
                stations.start(db, actor, None, task_ids, waiting)

        def finish(task_ids: list[str]) -> None:
            if task_ids:
                stations.finish(db, actor, None, task_ids, started)

        # 1: Bar diproses dan sudah lewat targetnya, Dapur masih menunggu.
        start(ids(orders[0], BAR_ID))
        for task_id in ids(orders[0], BAR_ID):
            age(db, task_id, arrived=9, started=6)
        for task_id in ids(orders[0], KITCHEN_ID):
            age(db, task_id, arrived=9)
        # 2 dan 3: baru masuk antrean.
        for order, minutes in ((orders[1], 2), (orders[2], 1)):
            for station_id in (BAR_ID, KITCHEN_ID):
                for task_id in ids(order, station_id):
                    age(db, task_id, arrived=minutes)
        # 4: Bar baru dimulai, masih ada sisa waktu.
        start(ids(orders[3], BAR_ID))
        for task_id in ids(orders[3], BAR_ID):
            age(db, task_id, arrived=3, started=1)
        # 5: pengajuan pembatalan yang menunggu keputusan.
        db.add(CancellationRequest(id=new_id(), order_id=orders[4].id, outlet_id=outlet.id, requested_by_id=counter.id, reason="Pelanggan salah memilih menu", status=CancellationStatus.PENDING, created_at=stamp - timedelta(minutes=2)))
        db.commit()
        # 6: pesanan dibatalkan setelah masuk stasiun.
        orders[5].voided_at = stamp - timedelta(minutes=1)
        orders[5].void_reason = "Pelanggan membatalkan pesanan (data demo)"
        orders[5].voided_by_id = counter.id
        db.commit()
        # 7: Bar selesai, menunggu diantar Waiters.
        start(ids(orders[6], BAR_ID))
        finish(ids(orders[6], BAR_ID))
        # 8: Dapur selesai, menunggu diantar Waiters.
        start(ids(orders[7], KITCHEN_ID))
        finish(ids(orders[7], KITCHEN_ID))

        valid = [order for order in orders if order.voided_at is None]
        session.system_revenue = sum((order.total for order in valid), Decimal("0"))
        session.cash_revenue = session.system_revenue
        db.commit()
        db.execute(update(Order).where(Order.id.like(f"{PREFIX}-%")).values(served_at=None))
        db.commit()
        print(f"Selesai. {len(orders)} pesanan demo dan sesi kasir terbuka dibuat di cabang {outlet.name}.")
        print("Buka Papan Stasiun di tablet. Stasiun di cabang ini ditampilkan sebagai tab: Bar, Dapur, Waiters, dan Kasir.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
