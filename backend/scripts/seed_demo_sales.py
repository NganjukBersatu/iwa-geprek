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
from app.core.permissions.registry import CASHIER_EXAMPLE  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.core.settings import settings  # noqa: E402
from app.core.visitors import seed_defaults as seed_visitor_lists  # noqa: E402
from app.models.cash_session import CashSession, CashSessionStatus  # noqa: E402
from app.models.category import Category  # noqa: E402
from app.models.expense import Expense, FundSource  # noqa: E402
from app.models.extra import Extra, MenuExtra  # noqa: E402
from app.models.menu_item import MenuItem  # noqa: E402
from app.models.order_item_option import OrderItemOption  # noqa: E402
from app.models.promo import Promo  # noqa: E402
from app.models.variant import MenuVariantGroup, VariantChoice, VariantGroup  # noqa: E402
from app.models.order import Order  # noqa: E402
from app.models.order_item import OrderItem  # noqa: E402
from app.models.outlet import Outlet  # noqa: E402
from app.models.payment_method import PaymentMethod  # noqa: E402
from app.models.role import Role  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.visitor import VisitorCategory, VisitorGender  # noqa: E402
from app.core.catalog.menu import PHOTO_FOLDER  # noqa: E402
from app.core.storage import files  # noqa: E402
from app.core.uploads.file import KIND_PHOTO  # noqa: E402
from app.core.uploads.formats import identify  # noqa: E402
from scripts import demo_catalog  # noqa: E402

PREFIX = "demo-"
CONFIRMATION = "ya"
DAYS = 240
COST_RATIO = Decimal("0.35")
VOID_CHANCE = 0.02
DISCOUNT_CHANCE = 0.08
DISCOUNT_AMOUNT = Decimal("5000")
CASH_STEP = Decimal("5000")
MIN_SHIFT_MINUTES = 30
SERVED_AFTER_MINUTES = 8
DEMO_ROLE_ID = f"{PREFIX}kasir"
CASHIER_NAMES = (("demo.kasir1", "Kasir Demo Satu"), ("demo.kasir2", "Kasir Demo Dua"), ("demo.kasir3", "Kasir Demo Tiga"))

# Menu, harga, bobot, jam sesi, modal awal, dan pengeluaran contoh dibaca dari demo_catalog.json milik klien.
CATALOG = demo_catalog.load()
# Jenis opsi baris pesanan, sama dengan app.core.orders.options.
OPTION_VARIANT = "varian"
OPTION_EXTRA = "ekstra"
PROMO_KIND_TOTAL = "total"
PROMO_ACTIVATION_AUTO = "otomatis"
PROMO_RUNS_DAYS_AHEAD = 60
PERCENT = Decimal(100)
PAYMENT_WEIGHTS = {"tunai": 45, "qris": 40, "debit": 10, "transfer": 5}
DEMO_TABLES = (Expense, OrderItemOption, OrderItem, Order, CashSession, MenuVariantGroup, MenuExtra, VariantChoice, VariantGroup, Extra, Promo, MenuItem, Category, User, Role)


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
        # Per menu: kelompok varian beserta pilihan dan bobotnya, serta ekstra beserta peluangnya; dari katalog klien.
        self.variants: dict[str, list[tuple[VariantGroup, list[tuple[VariantChoice, int]]]]] = {}
        self.extras: dict[str, list[tuple[Extra, Decimal]]] = {}
        self.promos: list[tuple[Promo, demo_catalog.Promotion]] = []


def create_options(db: Session, plan: Plan, first_day: date) -> None:
    """Kelompok varian, ekstra, tautannya ke menu, dan promo dari katalog klien; semuanya berawalan demo- supaya bisa dihapus lagi."""
    groups: dict[str, tuple[VariantGroup, list[tuple[VariantChoice, int]]]] = {}
    for position, spec in enumerate(CATALOG.variant_groups):
        group = VariantGroup(id=new_id(), name=spec.name, required=spec.required, position=position, is_active=True, outlet_id=None)
        db.add(group)
        # Model ini tidak punya relasi ORM, jadi kelompok disimpan dulu supaya kunci asing pilihannya terpenuhi.
        db.flush()
        choices = []
        for order, choice_spec in enumerate(spec.choices):
            choice = VariantChoice(id=new_id(), group_id=group.id, name=choice_spec.name, color=None, position=order, is_active=True)
            db.add(choice)
            choices.append((choice, choice_spec.weight))
        groups[spec.name] = (group, choices)
    extras: dict[str, tuple[Extra, Decimal]] = {}
    for position, spec in enumerate(CATALOG.extras):
        extra = Extra(id=new_id(), name=spec.name, price=spec.price, outlet_ids=[plan.outlet.id], is_active=True, category_id=None, position=position)
        db.add(extra)
        extras[spec.name] = (extra, spec.rate)
    db.flush()
    by_name = {item.name: item for item, _ in plan.menu}
    for menu in CATALOG.menus():
        menu_item = by_name[menu.name]
        for name in menu.variant_groups:
            db.add(MenuVariantGroup(id=new_id(), menu_item_id=menu_item.id, group_id=groups[name][0].id))
            plan.variants.setdefault(menu_item.id, []).append(groups[name])
        for name in menu.extras:
            db.add(MenuExtra(id=new_id(), menu_item_id=menu_item.id, extra_id=extras[name][0].id))
            plan.extras.setdefault(menu_item.id, []).append(extras[name])
    stamp = now()
    for spec in CATALOG.promotions:
        promo = Promo(
            id=new_id(),
            name=spec.name,
            description=spec.description,
            kind=PROMO_KIND_TOTAL,
            discount_type=spec.discount_type,
            value=spec.value,
            applies_to=None,
            product_ids=None,
            minimum_spend=spec.minimum_spend,
            activation=PROMO_ACTIVATION_AUTO,
            starts_on=first_day,
            ends_on=stamp.astimezone(WIB).date() + timedelta(days=PROMO_RUNS_DAYS_AHEAD),
            is_active=True,
            outlet_id=None,
            created_at=stamp,
            updated_at=stamp,
        )
        db.add(promo)
        plan.promos.append((promo, spec))
    db.flush()


def options_for(rng: random.Random, plan: Plan, menu_item: MenuItem, item_id: str, qty: int) -> list[OrderItemOption]:
    """Satu pilihan per kelompok varian (wajib selalu, opsional setengahnya) dan ekstra sesuai peluangnya."""
    chosen: list[OrderItemOption] = []
    for group, choices in plan.variants.get(menu_item.id, []):
        if not group.required and rng.random() < 0.5:
            continue
        choice = rng.choices([choice for choice, _ in choices], weights=[weight for _, weight in choices])[0]
        chosen.append(OrderItemOption(id=new_id(), order_item_id=item_id, kind=OPTION_VARIANT, ref_id=choice.id, group_name=group.name, name=choice.name, color=None, price=Decimal(0), qty=1, unit_cost=None))
    for extra, rate in plan.extras.get(menu_item.id, []):
        if Decimal(str(rng.random())) < rate:
            chosen.append(OrderItemOption(id=new_id(), order_item_id=item_id, kind=OPTION_EXTRA, ref_id=extra.id, group_name=None, name=extra.name, color=None, price=extra.price, qty=qty, unit_cost=None))
    return chosen


def promo_for(rng: random.Random, plan: Plan, subtotal: Decimal) -> tuple[Promo | None, Decimal]:
    for promo, spec in plan.promos:
        if spec.minimum_spend is not None and subtotal < spec.minimum_spend:
            continue
        if Decimal(str(rng.random())) >= spec.rate:
            continue
        discount = (subtotal * spec.value / PERCENT).quantize(Decimal("1")) if spec.discount_type == "persen" else min(spec.value, subtotal)
        return promo, discount
    return None, Decimal(0)


def create_base(db: Session, plan: Plan) -> None:
    """Peran, kasir, kategori, dan menu demo; metode bayar dan daftar pengunjung dibuat bila cabangnya belum punya."""
    stamp = now()
    db.add(Role(id=DEMO_ROLE_ID, name="Kasir Demo", description="Data demo; aman dihapus.", permissions=sorted(CASHIER_EXAMPLE), is_default=False, sort_order=900, is_admin=False, is_protected=False, created_at=stamp, updated_at=stamp))
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
    for menu_category in CATALOG.menu_categories:
        category = Category(id=new_id(), kind="menu", name=menu_category.name, station=None, station_id=None)
        db.add(category)
        db.flush()
        for menu in menu_category.menus:
            menu_id = new_id()
            image_path = None
            if menu.image is not None:
                # Lewat pengenal unggahan yang sama dengan web admin, supaya foto contoh diperlakukan persis seperti foto yang diunggah pemilik.
                photo = identify(menu.image.suffix.lower(), menu.image.read_bytes())
                if photo is None or photo.kind != KIND_PHOTO:
                    raise demo_catalog.CatalogError(f"{menu.name}: {menu.image.name} bukan foto yang bisa dibaca")
                image_path = f"{PHOTO_FOLDER}/{menu_id}/{uuid.uuid4()}{photo.extension}"
                files.save(db, image_path, photo.content, photo.extension)
            menu_item = MenuItem(id=menu_id, name=menu.name, description=None, price=menu.price, category_id=category.id, image_path=image_path, is_available=True, has_temperature_variant=False, outlet_ids=[plan.outlet.id])
            db.add(menu_item)
            plan.menu.append((menu_item, menu.weight))
    if not plan.methods:
        seed_payment_methods(db, plan.outlet.id)
        plan.methods = {method.code: method for method in db.scalars(select(PaymentMethod).where(PaymentMethod.outlet_id == plan.outlet.id))}
    if not plan.categories:
        seed_visitor_lists(db, plan.outlet.id)
        plan.categories = list(db.scalars(select(VisitorCategory).where(VisitorCategory.outlet_id == plan.outlet.id, VisitorCategory.is_active)))
        plan.genders = list(db.scalars(select(VisitorGender).where(VisitorGender.outlet_id == plan.outlet.id, VisitorGender.is_active)))
    db.flush()


def build_order(rng: random.Random, plan: Plan, shift: CashSession, created_at: datetime, number: str) -> tuple[Order, list[OrderItem], list[OrderItemOption]]:
    order_id = new_id()
    items: list[OrderItem] = []
    options: list[OrderItemOption] = []
    for menu_item, _ in rng.choices(plan.menu, weights=[weight for _, weight in plan.menu], k=rng.randint(1, 4)):
        qty = rng.randint(1, 3)
        item_id = new_id()
        chosen = options_for(rng, plan, menu_item, item_id, qty)
        extras_total = sum((option.price * option.qty for option in chosen), Decimal("0"))
        options.extend(chosen)
        items.append(
            OrderItem(
                id=item_id,
                order_id=order_id,
                menu_item_id=menu_item.id,
                menu_item_name=menu_item.name,
                unit_price=menu_item.price,
                unit_cost=(menu_item.price * COST_RATIO).quantize(Decimal("1")),
                qty=qty,
                subtotal=menu_item.price * qty + extras_total,
                note=None,
            )
        )
    subtotal = sum((item.subtotal for item in items), Decimal("0"))
    promo, discount = promo_for(rng, plan, subtotal) if plan.promos else (None, Decimal("0"))
    if promo is None and not plan.promos and rng.random() < DISCOUNT_CHANCE and subtotal > DISCOUNT_AMOUNT:
        discount = DISCOUNT_AMOUNT
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
        promo_id=promo.id if promo is not None else None,
        discount=discount,
        total=total,
        created_at=created_at,
        voided_at=created_at + timedelta(minutes=5) if voided else None,
        void_reason="Salah input pesanan (data demo)" if voided else None,
        voided_by_id=plan.owner.id if voided else None,
        serving_status="selesai",
        served_at=created_at + timedelta(minutes=SERVED_AFTER_MINUTES),
    )
    return order, items, options


def build_expense(rng: random.Random, plan: Plan, shift: CashSession, created_at: datetime) -> Expense:
    item = rng.choice(CATALOG.expenses)
    return Expense(
        id=new_id(),
        outlet_id=plan.outlet.id,
        cash_session_id=shift.id,
        cashier_id=shift.cashier_id,
        routine_item_id=None,
        item_name=item.name,
        amount=Decimal(rng.randrange(item.low, item.high + 1, 5000)),
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
    for start_clock, end_clock in CATALOG.shifts:
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
            opening_cash=CATALOG.opening_cash,
            system_revenue=Decimal("0"),
            cash_revenue=Decimal("0"),
            drawer_expenses=Decimal("0"),
            status=CashSessionStatus.CLOSED if ended else CashSessionStatus.OPEN,
        )
        span = int((window_end - opened).total_seconds() // 60)
        moments = sorted(opened + timedelta(minutes=rng.randint(2, max(3, span - 2))) for _ in range(round(rng.randint(*CATALOG.orders_per_session) * busy * growth)))
        built = [build_order(rng, plan, session, moment, f"DEMO-{day:%Y%m%d}-{sessions + 1}{index:03d}") for index, moment in enumerate(moments, start=1)]
        spent = [build_expense(rng, plan, session, opened + timedelta(minutes=rng.randint(10, max(11, span - 5)))) for _ in range(rng.randint(0, 2) if CATALOG.expenses else 0)]

        valid = [order for order, _, _ in built if order.voided_at is None]
        session.system_revenue = sum((order.total for order in valid), Decimal("0"))
        session.cash_revenue = sum((order.total for order in valid if order.payment_method == "tunai"), Decimal("0"))
        session.drawer_expenses = sum((expense.amount for expense in spent if expense.fund_source == FundSource.DRAWER_CASH), Decimal("0"))
        if ended:
            difference = Decimal(rng.choice((0, 0, 0, 0, -5000, 5000, -10000)))
            session.actual_cash = CATALOG.opening_cash + session.cash_revenue - session.drawer_expenses + difference
            session.difference = difference

        money_trail.act_as(db, plan.owner.id)
        db.add(session)
        db.flush()
        db.add_all(order for order, _, _ in built)
        db.flush()
        db.add_all(item for _, items, _ in built for item in items)
        db.flush()
        db.add_all(option for _, _, options in built for option in options)
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
        print(f"Rencana: {DAYS} hari terakhir, {len(CATALOG.shifts)} sesi kas per hari, sekitar {CATALOG.orders_per_session[0]} sampai {CATALOG.orders_per_session[1]} pesanan per sesi, {len(CASHIER_NAMES)} kasir demo, {len(CATALOG.menus())} menu demo.")
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
            create_options(db, plan, first_day)
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
