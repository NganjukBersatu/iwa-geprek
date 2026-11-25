"""Data contoh cabang pertama dari demo_catalog.json milik klien: titik absen, pengaturan struk, dan metode bayar yang siap dipakai kasir.

    python scripts/seed_demo_branch.py           # menampilkan rencana dan menulis tidak apa pun
    python scripts/seed_demo_branch.py --tulis   # menulis setelah Anda mengetik "ya"

Hanya mengisi bagian yang masih kosong, sehingga pengaturan yang sudah diisi orang tidak pernah ditimpa. Metode bayar non-tunai yang
dicatat di katalog diberi catatan dan gambar kode QR contoh, karena kasir hanya membuka metode yang gambar dan catatannya lengkap.
"""
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402
from sqlalchemy.exc import ProgrammingError  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core import branch_settings, money_trail  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.core.settings import settings  # noqa: E402
from app.core.storage import files  # noqa: E402
from app.models.outlet import Outlet  # noqa: E402
from app.models.payment_method import PaymentMethod  # noqa: E402
from app.models.user import User  # noqa: E402
from scripts import demo_catalog  # noqa: E402
from web.management.payment_methods.constants import IMAGE_FOLDER  # noqa: E402

CONFIRMATION = "ya"
QR_EXTENSION = ".png"
QR_SCALE = 12
QR_BORDER_MODULES = 4


def qr_image(text: str) -> bytes:
    """Gambar kode QR berisi catatan metode bayar; hanya contoh untuk data demo, bukan kode pembayaran sungguhan."""
    import cv2
    import numpy as np

    matrix = cv2.QRCodeEncoder.create().encode(text)
    padded = np.pad(matrix, QR_BORDER_MODULES * (matrix.shape[0] // max(1, matrix.shape[0])), constant_values=255)
    scaled = cv2.resize(padded, None, fx=QR_SCALE, fy=QR_SCALE, interpolation=cv2.INTER_NEAREST)
    ok, encoded = cv2.imencode(QR_EXTENSION, scaled)
    if not ok:
        raise RuntimeError("kode QR contoh tidak bisa dibuat")
    return encoded.tobytes()


def fill_branch(db: Session, outlet: Outlet, branch: demo_catalog.Branch) -> list[str]:
    done = []
    if outlet.latitude is None and branch.latitude is not None:
        outlet.latitude = branch.latitude
        outlet.longitude = branch.longitude
        done.append("titik absen")
    if branch.attendance_radius_meters is not None and outlet.attendance_radius_meters != branch.attendance_radius_meters:
        outlet.attendance_radius_meters = branch.attendance_radius_meters
        done.append("radius absen")
    row = branch_settings.ensure(db, outlet.id)
    if not row.address and not row.phone and not row.receipt_greeting:
        row.address = branch.address
        row.phone = branch.phone
        row.complaint_number = branch.complaint_number
        row.receipt_greeting = branch.receipt_greeting
        row.social = [{"icon": icon, "handle": handle} for icon, handle in branch.social]
        row.wifi = [{"area": area, "ssid": ssid} for area, ssid in branch.wifi]
        row.wifi_password = branch.wifi_password
        done.append("pengaturan struk")
    return done


def fill_payments(db: Session, outlet: Outlet, notes: tuple[tuple[str, str], ...]) -> list[str]:
    methods = {method.code: method for method in db.scalars(select(PaymentMethod).where(PaymentMethod.outlet_id == outlet.id))}
    done = []
    for code, note in notes:
        method = methods.get(code)
        if method is None or method.image_path or (method.note or "").strip():
            continue
        path = f"{IMAGE_FOLDER}/{method.id}/{uuid.uuid4()}{QR_EXTENSION}"
        files.save(db, path, qr_image(f"{method.label} {outlet.name}: {note}"), QR_EXTENSION)
        method.image_path = path
        method.note = note
        done.append(method.label)
    return done


def main() -> int:
    args = sys.argv[1:]
    url = make_url(settings.database_url)
    target = f"{url.host}:{url.port}/{url.database}"
    print(f"Database: {target}")
    catalog = demo_catalog.load()
    if catalog.branch is None and not catalog.payment_notes:
        print("Katalog tidak berisi data cabang atau metode bayar. Tidak ada yang diubah.")
        return 0
    with SessionLocal() as db:
        try:
            outlet = db.scalar(select(Outlet).order_by(Outlet.created_at, Outlet.id).limit(1))
        except ProgrammingError:
            db.rollback()
            print("Tabel belum ada di database ini. Jalankan dulu: python -m alembic upgrade head. Tidak ada yang diubah.")
            return 1
        owner = db.scalar(select(User).where(User.role_id == "owner", User.deleted_at.is_(None), User.is_active).limit(1))
        if outlet is None or owner is None:
            print("Belum ada cabang atau akun pemilik. Jalankan dulu scripts/create_owner.py --tulis. Tidak ada yang diubah.")
            return 1
        print(f"Cabang tujuan: {outlet.name}")
        if "--tulis" not in args:
            print("Belum ada yang ditulis. Jalankan dengan --tulis untuk membuatnya.")
            return 0
        if input(f'Ketik "{CONFIRMATION}" untuk menulis ke {target}: ').strip().lower() != CONFIRMATION:
            print("Dibatalkan. Tidak ada yang ditulis.")
            return 1
        money_trail.act_as(db, owner.id)
        done = (fill_branch(db, outlet, catalog.branch) if catalog.branch else []) + fill_payments(db, outlet, catalog.payment_notes)
        db.commit()
    print(f"Selesai. Diisi: {', '.join(done) if done else 'tidak ada (semuanya sudah terisi)'}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
