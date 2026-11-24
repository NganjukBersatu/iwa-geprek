"""Data demo untuk halaman Dana Lebih dan Pengeluaran di tablet: beberapa pesanan non-tunai yang dibayar lebih, dan beberapa pengeluaran sesi berjalan.

    python scripts/seed_demo_finance.py           # menampilkan rencana dan menulis tidak apa pun
    python scripts/seed_demo_finance.py --tulis   # menulis data demo setelah Anda mengetik "ya"
    python scripts/seed_demo_finance.py --hapus   # menghapus semua data demo ini setelah Anda mengetik "ya"

Hanya untuk database pengembangan; database tujuannya (DATABASE_URL) ditampilkan sebelum menulis.
Datanya masuk ke sesi kasir yang sedang terbuka milik akun non-demo di cabang menu demo (sesi yang dibuka di tablet), supaya terlihat oleh kasir itu.
Butuh data dari scripts/seed_demo_sales.py. Semua barisnya berawalan "demo-fin" supaya bisa dihapus lagi tanpa menyentuh data demo lain.
"""
import sys
import uuid
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import delete, func, select  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402
from sqlalchemy.exc import ProgrammingError  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.clock import now  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.core.orders import overpayment, stages  # noqa: E402
from app.core.orders.order_types import DINE_IN, TAKE_AWAY  # noqa: E402
from app.core.settings import settings  # noqa: E402
from app.models.cash_session import CashSession, CashSessionStatus  # noqa: E402
from app.models.expense import Expense, FundSource  # noqa: E402
from app.models.menu_item import MenuItem  # noqa: E402
from app.models.order import Order  # noqa: E402
from app.models.order_item import OrderItem  # noqa: E402
from app.models.overpayment import Overpayment  # noqa: E402
from app.models.payment_method import PaymentMethod  # noqa: E402
from app.models.user import User  # noqa: E402
from scripts import demo_catalog  # noqa: E402

PREFIX = "demo-fin"
CONFIRMATION = "ya"
COST_RATIO = Decimal("0.35")

# (jenis, meja, jumlah tiap baris, dibayar lebih dari total, menit sejak dibuat, dibatalkan); menunya diambil bergiliran dari katalog klien.
ORDER_SHAPES = (
    (DINE_IN, "3", (2, 1), 6000, 95, False),
    (TAKE_AWAY, None, (1,), 3000, 80, False),
    (DINE_IN, "6", (2, 1), 1000, 60, False),
    (TAKE_AWAY, None, (3,), 6000, 40, False),
    (DINE_IN, "2", (1, 1), 8000, 25, True),
    (DINE_IN, "8", (1,), 500, 10, False),
)
# (sumber dana, catatan, menit sejak dicatat) untuk pengeluaran contoh dari katalog klien, berurutan.
EXPENSE_SLOTS = (
    (FundSource.DRAWER_CASH, "Supplier langganan", 110),
    (FundSource.DRAWER_CASH, None, 100),
    (FundSource.OTHER_FUNDS, None, 90),
    (FundSource.DRAWER_CASH, None, 70),
    (FundSource.OTHER_FUNDS, None, 55),
    (FundSource.DRAWER_CASH, None, 30),
    (FundSource.DRAWER_CASH, None, 15),
)
EXPENSE_ROUNDING = 1000


def planned_orders(menu_names: list[str]) -> list[tuple]:
    """Pesanan contoh dengan menu bergiliran dari katalog, sehingga setiap klien melihat menunya sendiri."""
    plan = []
    position = 0
    for order_type, table, quantities, extra, minutes, voided in ORDER_SHAPES:
        lines = []
        for qty in quantities:
            lines.append((menu_names[position % len(menu_names)], qty))
            position += 1
        plan.append((order_type, table, lines, extra, minutes, voided))
    return plan


def planned_expenses(catalog: demo_catalog.Catalog) -> list[tuple[str, int, FundSource, str | None, int]]:
    """Pengeluaran contoh dari daftar pengeluaran katalog, dengan nominal di tengah rentangnya."""
    return [
        (item.name, ((item.low + item.high) // 2 + EXPENSE_ROUNDING // 2) // EXPENSE_ROUNDING * EXPENSE_ROUNDING, source, note, minutes)
        # Paling banyak sebanyak slot yang ada; pengeluaran katalog selebihnya tidak dipakai di contoh hari ini.
        for item, (source, note, minutes) in zip(catalog.expenses, EXPENSE_SLOTS, strict=False)
    ]


def new_id() -> str:
    return f"{PREFIX}-{uuid.uuid4()}"


def delete_demo(db: Session) -> None:
    order_ids = select(Order.id).where(Order.id.like(f"{PREFIX}-%"))
    drawer = db.execute(select(Expense.cash_session_id, func.sum(Expense.amount)).where(Expense.id.like(f"{PREFIX}-%"), Expense.fund_source == FundSource.DRAWER_CASH).group_by(Expense.cash_session_id)).all()
    revenue = db.execute(select(Order.cash_session_id, func.sum(Order.total)).where(Order.id.like(f"{PREFIX}-%"), Order.voided_at.is_(None)).group_by(Order.cash_session_id)).all()
    for session_id, amount in drawer:
        session = db.get(CashSession, session_id)
        if session is not None:
            session.drawer_expenses = session.drawer_expenses - amount
    for session_id, amount in revenue:
        session = db.get(CashSession, session_id)
        if session is not None:
            session.system_revenue = session.system_revenue - amount
    db.execute(delete(Overpayment).where(Overpayment.order_id.in_(order_ids)))
    db.execute(delete(OrderItem).where(OrderItem.order_id.in_(order_ids)))
    db.execute(delete(Order).where(Order.id.like(f"{PREFIX}-%")))
    db.execute(delete(Expense).where(Expense.id.like(f"{PREFIX}-%")))
    db.commit()


def main() -> int:
    mode = "--tulis" if "--tulis" in sys.argv[1:] else "--hapus" if "--hapus" in sys.argv[1:] else None
    url = make_url(settings.database_url)
    target = f"{url.host}:{url.port}/{url.database}"
    print(f"Database: {target}")
    with SessionLocal() as db:
        try:
            existing = db.scalar(select(func.count()).select_from(Order).where(Order.id.like(f"{PREFIX}-%"))) or 0
        except ProgrammingError:
            db.rollback()
            print("Tabel belum ada di database ini. Jalankan dulu: python -m alembic upgrade head. Tidak ada yang diubah.")
            return 1

        if mode == "--hapus":
            print(f"Akan menghapus {existing} pesanan demo beserta kelebihan dan pengeluaran demonya.")
            if input(f'Ketik "{CONFIRMATION}" untuk melanjutkan: ').strip().lower() != CONFIRMATION:
                print("Dibatalkan. Tidak ada yang dihapus.")
                return 1
            delete_demo(db)
            print("Selesai. Data demo dihapus.")
            return 0

        menu = {m.name: m for m in db.scalars(select(MenuItem).where(MenuItem.id.like("demo-%"))).all()}
        first_menu = next(iter(menu.values()), None)
        outlet_id = first_menu.outlet_ids[0] if first_menu is not None and first_menu.outlet_ids else None
        session = None
        if outlet_id is not None:
            session = db.scalars(
                select(CashSession)
                .join(User, User.id == CashSession.cashier_id)
                .where(CashSession.outlet_id == outlet_id, CashSession.status == CashSessionStatus.OPEN, CashSession.id.not_like("demo-%"), User.username.not_like("demo.%"))
                .order_by(CashSession.opened_at.desc())
                .limit(1)
            ).first()
        method = db.scalars(select(PaymentMethod).where(PaymentMethod.outlet_id == outlet_id, PaymentMethod.code == "qris")).first() if outlet_id else None

        print("Rencana: 6 pesanan QRIS yang dibayar lebih (satu pesanan dibatalkan) dan 7 pengeluaran, semuanya hari ini di sesi kasir yang sedang terbuka.")
        if existing:
            print("Data demo ini sudah ada. Jalankan dengan --hapus dulu bila ingin membuatnya ulang. Tidak ada yang diubah.")
            return 0
        if session is None or method is None or not menu:
            print("Tidak ada sesi kasir terbuka milik akun non-demo di cabang menu demo, atau data demo penjualan belum ada.")
            print("Buka sesi kasir di tablet dulu, dan pastikan scripts/seed_demo_sales.py --tulis sudah dijalankan. Tidak ada yang diubah.")
            return 1
        cashier = db.get(User, session.cashier_id)
        print(f"Sesi: milik {cashier.username}, dibuka {session.opened_at:%d %b %H:%M}")
        if mode != "--tulis":
            print("Belum ada yang ditulis. Jalankan dengan --tulis untuk membuatnya.")
            return 0
        if input(f'Akan menulis ke database {target}. Ketik "{CONFIRMATION}" untuk melanjutkan: ').strip().lower() != CONFIRMATION:
            print("Dibatalkan. Tidak ada yang ditulis.")
            return 1

        stamp = now()
        # Waktu catatan tidak boleh mendahului pembukaan sesi.
        floor = session.opened_at
        drawer_total = Decimal("0")
        revenue_total = Decimal("0")
        catalog = demo_catalog.load()
        for index, (order_type, table, lines, extra, minutes, voided) in enumerate(planned_orders([item.name for item in catalog.menus()]), start=1):
            created = max(stamp - timedelta(minutes=minutes), floor + timedelta(minutes=index))
            order_id = new_id()
            total = Decimal("0")
            items = []
            for name, qty in lines:
                found = menu[name]
                total += found.price * qty
                items.append(
                    OrderItem(id=new_id(), order_id=order_id, menu_item_id=found.id, menu_item_name=found.name, unit_price=found.price, unit_cost=(found.price * COST_RATIO).quantize(Decimal("1")), qty=qty, subtotal=found.price * qty, note=None)
                )
            order = Order(
                id=order_id,
                cash_session_id=session.id,
                outlet_id=outlet_id,
                cashier_id=session.cashier_id,
                customer_name=None,
                table_no=table,
                order_type=order_type,
                visitor_category_id=None,
                visitor_category_label=None,
                visitor_gender_id=None,
                visitor_gender_label=None,
                note_id=None,
                note_label=None,
                receipt_number=f"DEMO-FIN-{index:03d}",
                client_id=None,
                payment_method=method.code,
                payment_method_label=method.label,
                payment_method_id=method.id,
                cash_received=total + extra,
                promo_id=None,
                discount=Decimal("0"),
                total=total,
                created_at=created,
                voided_at=created + timedelta(minutes=3) if voided else None,
                void_reason="Pelanggan membatalkan pesanan (data demo)" if voided else None,
                voided_by_id=session.cashier_id if voided else None,
                serving_status=stages.first_code(db, outlet_id),
                served_at=None,
            )
            db.add(order)
            db.add_all(items)
            db.flush()
            overpayment.sync(db, order, method)
            if not voided:
                revenue_total += total
        for name, amount, source, note, minutes in planned_expenses(catalog):
            db.add(
                Expense(
                    id=new_id(),
                    outlet_id=outlet_id,
                    cash_session_id=session.id,
                    cashier_id=session.cashier_id,
                    routine_item_id=None,
                    item_name=name,
                    amount=Decimal(amount),
                    fund_source=source,
                    note=note,
                    buyer=None,
                    receipt_path=None,
                    ingredient_id=None,
                    quantity=None,
                    unit_id=None,
                    created_at=max(stamp - timedelta(minutes=minutes), floor + timedelta(minutes=1)),
                )
            )
            if source == FundSource.DRAWER_CASH:
                drawer_total += Decimal(amount)
        session.system_revenue = session.system_revenue + revenue_total
        session.drawer_expenses = session.drawer_expenses + drawer_total
        db.commit()
        print("Selesai. 6 pesanan, kelebihannya, dan 7 pengeluaran dibuat di sesi yang sedang terbuka.")
        print("Buka Dana Lebih dan Pengeluaran di tablet (rentang tanggal bawaan: hari ini).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
