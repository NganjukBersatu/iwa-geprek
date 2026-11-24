"""Data demo penjualan untuk melihat dasbor web; semua barisnya berawalan "demo-" supaya bisa dihapus lagi.

    python scripts/seed_demo_sales.py           # menampilkan rencana dan menulis tidak apa pun
    python scripts/seed_demo_sales.py --tulis   # menulis data demo setelah Anda mengetik "ya"
    python scripts/seed_demo_sales.py --hapus   # menghapus semua data demo setelah Anda mengetik "ya"

Hanya untuk database pengembangan: ia menulis ke cabang pertama, dan database tujuannya (DATABASE_URL) ditampilkan sebelum menulis.
Akun kasir demo tidak bisa dipakai masuk karena kata sandinya acak dan tidak pernah disimpan.
Butuh akun pemilik dan cabang yang dibuat lebih dulu oleh scripts/create_owner.py.
"""
import random
import secrets
import sys
import uuid
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import delete, func, select  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402
from sqlalchemy.exc import IntegrityError, ProgrammingError  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core import money_trail  # noqa: E402
from app.core.clock import WIB, now  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.core.finance.payment_methods import seed_defaults as seed_payment_methods  # noqa: E402
from app.core.orders.order_types import DINE_IN, TAKE_AWAY  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.core.settings import settings  # noqa: E402
from app.core.visitors import seed_defaults as seed_visitor_lists  # noqa: E402
from app.models.cash_session import CashSession, CashSessionStatus  # noqa: E402
from app.models.category import Category  # noqa: E402
from app.models.expense import Expense, FundSource  # noqa: E402
from app.models.menu_item import MenuItem  # noqa: E402
from app.models.order import Order  # noqa: E402
from app.models.order_item import OrderItem  # noqa: E402
from app.models.outlet import Outlet  # noqa: E402
from app.models.payment_method import PaymentMethod  # noqa: E402
from app.models.role import Role  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.visitor import VisitorCategory, VisitorGender  # noqa: E402

PREFIX = "demo-"
CONFIRMATION = "ya"
DAYS = 240
OPENING_CASH = Decimal("500000")
COST_RATIO = Decimal("0.35")
VOID_CHANCE = 0.02
DISCOUNT_CHANCE = 0.08
DISCOUNT_AMOUNT = Decimal("5000")
CASH_STEP = Decimal("5000")
MIN_SHIFT_MINUTES = 30
SERVED_AFTER_MINUTES = 8
DEMO_ROLE_ID = f"{PREFIX}kasir"
CASHIER_NAMES = (("demo.kasir1", "Kasir Demo Satu"), ("demo.kasir2", "Kasir Demo Dua"), ("demo.kasir3", "Kasir Demo Tiga"))

# (nama kategori, [(nama menu, harga, bobot popularitas)]); nama kategori berakhiran "Demo" supaya tidak bentrok dengan kategori asli.
CATALOG = (
    ("Kopi Demo", (("Kopi Susu", 22000, 10), ("Americano", 18000, 5), ("Latte", 25000, 6), ("Cappuccino", 25000, 5))),
    ("Non-Kopi Demo", (("Matcha Latte", 27000, 5), ("Cokelat Panas", 24000, 3), ("Teh Lemon", 16000, 4))),
    ("Roti Demo", (("Croissant", 20000, 7), ("Cinnamon Roll", 24000, 6), ("Roti Bakar Cokelat", 18000, 4))),
    ("Dessert Demo", (("Cheesecake", 32000, 4), ("Brownies", 22000, 5), ("Pudding Karamel", 20000, 3))),
)
PAYMENT_WEIGHTS = {"tunai": 45, "qris": 40, "debit": 10, "transfer": 5}
SHIFT_WINDOWS = ((time(8, 0), time(15, 0)), (time(15, 0), time(22, 0)))
EXPENSE_POOL = (
    ("Susu segar", 60000, 180000),
    ("Biji kopi", 150000, 400000),
    ("Es batu", 20000, 50000),
    ("Gas elpiji", 90000, 120000),
    ("Kemasan gelas", 80000, 200000),
    ("Gula dan sirup", 50000, 150000),
    ("Tepung dan mentega", 100000, 300000),
)
DEMO_TABLES = (Expense, OrderItem, Order, CashSession, MenuItem, Category, User, Role)


def new_id() -> str:
    return f"{PREFIX}{uuid.uuid4()}"


def at_wib(day: date, clock: time) -> datetime:
    return datetime.combine(day, clock, tzinfo=WIB)


def demo_count(db: Session, model) -> int:
    column = model.order_id if model is OrderItem else model.id
    return db.scalar(select(func.count()).select_from(model).where(column.like(f"{PREFIX}%"))) or 0


def delete_demo(db: Session) -> None:
    for model in DEMO_TABLES:
        column = model.order_id if model is OrderItem else model.id
        db.execute(delete(model).where(column.like(f"{PREFIX}%")))
    db.commit()


class Plan:
    """Bahan yang dipakai semua hari: cabang, pemilik, kasir demo, menu, metode bayar, dan daftar pengunjung."""

    def __init__(self, db: Session, outlet: Outlet, owner: User) -> None:
        self.outlet = outlet
        self.owner = owner
        self.cashiers: list[User] = []
        self.menu: list[tuple[MenuItem, int]] = []
        self.methods = {method.code: method for method in db.scalars(select(PaymentMethod).where(PaymentMethod.outlet_id == outlet.id))}
        self.categories = list(db.scalars(select(VisitorCategory).where(VisitorCategory.outlet_id == outlet.id, VisitorCategory.is_active)))
        self.genders = list(db.scalars(select(VisitorGender).where(VisitorGender.outlet_id == outlet.id, VisitorGender.is_active)))


def create_base(db: Session, plan: Plan) -> None:
    """Peran, kasir, kategori, dan menu demo; metode bayar dan daftar pengunjung dibuat bila cabangnya belum punya."""
    stamp = now()
    db.add(Role(id=DEMO_ROLE_ID, name="Kasir Demo", description="Data demo; aman dihapus.", permissions=[], is_default=False, sort_order=900, is_admin=False, is_protected=False, created_at=stamp, updated_at=stamp))
    db.flush()
    for username, name in CASHIER_NAMES:
        cashier = User(
            id=new_id(),
            name=name,
            username=username,
            password_hash=hash_password(secrets.token_urlsafe(24)),
            role_id=DEMO_ROLE_ID,
            outlet_id=plan.outlet.id,
            is_active=True,
            joined_date=(stamp.astimezone(WIB) - timedelta(days=DAYS + 30)).date(),
            created_at=stamp,
        )
        db.add(cashier)
        plan.cashiers.append(cashier)
    for category_name, items in CATALOG:
        category = Category(id=new_id(), kind="menu", name=category_name, station=None, station_id=None)
        db.add(category)
        db.flush()
        for name, price, weight in items:
            menu_item = MenuItem(id=new_id(), name=name, description=None, price=Decimal(price), category_id=category.id, image_path=None, is_available=True, has_temperature_variant=False, outlet_ids=[plan.outlet.id])
            db.add(menu_item)
            plan.menu.append((menu_item, weight))
    if not plan.methods:
        seed_payment_methods(db, plan.outlet.id)
        plan.methods = {method.code: method for method in db.scalars(select(PaymentMethod).where(PaymentMethod.outlet_id == plan.outlet.id))}
    if not plan.categories:
        seed_visitor_lists(db, plan.outlet.id)
        plan.categories = list(db.scalars(select(VisitorCategory).where(VisitorCategory.outlet_id == plan.outlet.id, VisitorCategory.is_active)))
        plan.genders = list(db.scalars(select(VisitorGender).where(VisitorGender.outlet_id == plan.outlet.id, VisitorGender.is_active)))
    db.flush()


def build_order(rng: random.Random, plan: Plan, shift: CashSession, created_at: datetime, number: str) -> tuple[Order, list[OrderItem]]:
    order_id = new_id()
    items: list[OrderItem] = []
    for menu_item, _ in rng.choices(plan.menu, weights=[weight for _, weight in plan.menu], k=rng.randint(1, 4)):
        qty = rng.randint(1, 3)
        items.append(
            OrderItem(
                id=new_id(),
                order_id=order_id,
                menu_item_id=menu_item.id,
                menu_item_name=menu_item.name,
                unit_price=menu_item.price,
                unit_cost=(menu_item.price * COST_RATIO).quantize(Decimal("1")),
                qty=qty,
                subtotal=menu_item.price * qty,
                note=None,
            )
        )
    subtotal = sum((item.subtotal for item in items), Decimal("0"))
    discount = DISCOUNT_AMOUNT if rng.random() < DISCOUNT_CHANCE and subtotal > DISCOUNT_AMOUNT else Decimal("0")
    total = subtotal - discount

    codes = [code for code in PAYMENT_WEIGHTS if code in plan.methods] or list(plan.methods)
    code = rng.choices(codes, weights=[PAYMENT_WEIGHTS.get(code, 1) for code in codes])[0]
    method = plan.methods[code]
    received = (total / CASH_STEP).to_integral_value(rounding="ROUND_CEILING") * CASH_STEP if code == "tunai" else None

    category = rng.choice(plan.categories) if plan.categories else None
    gender = rng.choice(plan.genders) if plan.genders and category is not None and category.asks_gender else None
    voided = rng.random() < VOID_CHANCE
    order = Order(
        id=order_id,
        cash_session_id=shift.id,
        outlet_id=plan.outlet.id,
        cashier_id=shift.cashier_id,
        customer_name=None,
        table_no=None,
        order_type=rng.choice((DINE_IN, DINE_IN, TAKE_AWAY)),
        visitor_category_id=category.id if category else None,
        visitor_category_label=category.name if category else None,
        visitor_gender_id=gender.id if gender else None,
        visitor_gender_label=gender.name if gender else None,
        note_id=None,
        note_label=None,
        receipt_number=number,
        client_id=None,
        payment_method=method.code,
        payment_method_label=method.label,
        payment_method_id=method.id,
        cash_received=received,
        promo_id=None,
        discount=discount,
        total=total,
        created_at=created_at,
        voided_at=created_at + timedelta(minutes=5) if voided else None,
        void_reason="Salah input pesanan (data demo)" if voided else None,
        voided_by_id=plan.owner.id if voided else None,
        serving_status="selesai",
        served_at=created_at + timedelta(minutes=SERVED_AFTER_MINUTES),
    )
    return order, items


def build_expense(rng: random.Random, plan: Plan, shift: CashSession, created_at: datetime) -> Expense:
    name, low, high = rng.choice(EXPENSE_POOL)
    return Expense(
        id=new_id(),
        outlet_id=plan.outlet.id,
        cash_session_id=shift.id,
        cashier_id=shift.cashier_id,
        routine_item_id=None,
        item_name=name,
        amount=Decimal(rng.randrange(low, high + 1, 5000)),
        fund_source=FundSource.DRAWER_CASH if rng.random() < 0.7 else FundSource.OTHER_FUNDS,
        note=None,
        buyer=None,
        receipt_path=None,
        ingredient_id=None,
        quantity=None,
        unit_id=None,
        created_at=created_at,
    )


def seed_day(db: Session, rng: random.Random, plan: Plan, day: date, day_index: int, current: datetime) -> tuple[int, int, int]:
    """Menulis semua sesi kas, pesanan, dan pengeluaran satu hari; mengembalikan jumlah sesi, pesanan, dan pengeluaran."""
    # Akhir pekan lebih ramai, dan penjualan naik pelan dari bulan ke bulan.
    busy = 1.4 if day.weekday() >= 4 else 1.0
    growth = 0.7 + 0.3 * (day_index / DAYS)
    sessions = orders = expenses = 0
    for start_clock, end_clock in SHIFT_WINDOWS:
        opened = at_wib(day, start_clock)
        window_end = min(at_wib(day, end_clock), current)
        if window_end - opened < timedelta(minutes=MIN_SHIFT_MINUTES):
            continue
        ended = at_wib(day, end_clock) <= current
        cashier = rng.choice(plan.cashiers)
        session = CashSession(
            id=new_id(),
            outlet_id=plan.outlet.id,
            cashier_id=cashier.id,
            shift_code_id=None,
            shift_code=None,
            shift_code_color=None,
            opened_at=opened,
            closed_at=at_wib(day, end_clock) if ended else None,
            opening_cash=OPENING_CASH,
            system_revenue=Decimal("0"),
            cash_revenue=Decimal("0"),
            drawer_expenses=Decimal("0"),
            status=CashSessionStatus.CLOSED if ended else CashSessionStatus.OPEN,
        )
        span = int((window_end - opened).total_seconds() // 60)
        moments = sorted(opened + timedelta(minutes=rng.randint(2, max(3, span - 2))) for _ in range(round(rng.randint(7, 13) * busy * growth)))
        built = [build_order(rng, plan, session, moment, f"DEMO-{day:%Y%m%d}-{sessions + 1}{index:03d}") for index, moment in enumerate(moments, start=1)]
        spent = [build_expense(rng, plan, session, opened + timedelta(minutes=rng.randint(10, max(11, span - 5)))) for _ in range(rng.randint(0, 2))]

        valid = [order for order, _ in built if order.voided_at is None]
        session.system_revenue = sum((order.total for order in valid), Decimal("0"))
        session.cash_revenue = sum((order.total for order in valid if order.payment_method == "tunai"), Decimal("0"))
        session.drawer_expenses = sum((expense.amount for expense in spent if expense.fund_source == FundSource.DRAWER_CASH), Decimal("0"))
        if ended:
            difference = Decimal(rng.choice((0, 0, 0, 0, -5000, 5000, -10000)))
            session.actual_cash = OPENING_CASH + session.cash_revenue - session.drawer_expenses + difference
            session.difference = difference

        money_trail.act_as(db, plan.owner.id)
        db.add(session)
        db.flush()
        db.add_all(order for order, _ in built)
        db.flush()
        db.add_all(item for _, items in built for item in items)
        db.add_all(spent)
        db.flush()
        sessions += 1
        orders += len(built)
        expenses += len(spent)
    return sessions, orders, expenses


def main() -> int:
    args = sys.argv[1:]
    url = make_url(settings.database_url)
    target = f"{url.host}:{url.port}/{url.database}"
    print(f"Database: {target}")

    with SessionLocal() as db:
        try:
            existing = demo_count(db, Order)
        except ProgrammingError:
            db.rollback()
            print("Tabel belum ada di database ini. Jalankan dulu: python -m alembic upgrade head. Tidak ada yang diubah.")
            return 1

        if "--hapus" in args:
            print(f"Akan menghapus data demo: {existing} pesanan beserta sesi kas, pengeluaran, menu, kategori, dan kasir demo.")
            if input(f'Ketik "{CONFIRMATION}" untuk melanjutkan: ').strip().lower() != CONFIRMATION:
                print("Dibatalkan. Tidak ada yang dihapus.")
                return 1
            actor = db.scalar(select(User.id).where(User.role_id == "owner", User.deleted_at.is_(None), User.is_active).limit(1))
            if actor is not None:
                money_trail.act_as(db, actor)
            delete_demo(db)
            print("Selesai. Data demo dihapus.")
            return 0

        outlet = db.scalar(select(Outlet).order_by(Outlet.created_at, Outlet.id).limit(1))
        owner = db.scalar(select(User).where(User.role_id == "owner", User.deleted_at.is_(None), User.is_active).limit(1))
        if outlet is None or owner is None:
            print("Belum ada cabang atau akun pemilik. Jalankan dulu scripts/create_owner.py --tulis. Tidak ada yang diubah.")
            return 1
        if existing:
            print(f"Sudah ada {existing} pesanan demo. Hapus dulu dengan: python scripts/seed_demo_sales.py --hapus. Tidak ada yang diubah.")
            return 1

        print(f"Cabang tujuan: {outlet.name}")
        print(f"Rencana: {DAYS} hari terakhir, dua sesi kas per hari, sekitar 10 sampai 20 pesanan per sesi, {len(CASHIER_NAMES)} kasir demo, {sum(len(items) for _, items in CATALOG)} menu demo.")
        if "--tulis" not in args:
            print("Belum ada yang ditulis. Jalankan dengan --tulis untuk membuatnya.")
            return 0
        if input(f'Ketik "{CONFIRMATION}" untuk menulis ke {target}: ').strip().lower() != CONFIRMATION:
            print("Dibatalkan. Tidak ada yang ditulis.")
            return 1

        rng = random.Random(2026)
        plan = Plan(db, outlet, owner)
        current = now().astimezone(WIB)
        first_day = current.date() - timedelta(days=DAYS - 1)
        totals = [0, 0, 0]
        try:
            money_trail.act_as(db, owner.id)
            create_base(db, plan)
            for index in range(DAYS):
                for position, count in enumerate(seed_day(db, rng, plan, first_day + timedelta(days=index), index, current)):
                    totals[position] += count
                # Per 30 hari disimpan, supaya kegagalan di tengah tidak membuang semuanya dan transaksi tidak membengkak.
                if (index + 1) % 30 == 0:
                    db.commit()
                    print(f"  {index + 1}/{DAYS} hari tersimpan")
            db.commit()
        except IntegrityError as error:
            db.rollback()
            print(f"Gagal: data bertabrakan atau melanggar aturan database ({error.orig.__class__.__name__}: {error.orig}).")
            print("Yang sudah tersimpan per 30 hari tetap ada; hapus dengan --hapus lalu coba lagi.")
            return 1
        print(f"Selesai. {totals[0]} sesi kas, {totals[1]} pesanan, {totals[2]} pengeluaran demo ditulis.")
        print("Buka dasbor di web dan pilih periode 7 hari, 4 minggu, atau 8 bulan.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
