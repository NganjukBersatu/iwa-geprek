"""One time, on a new database: creates the owner role, the first owner account and, when there is no branch yet, the first branch.

A new database has no role, no account and no branch, so nobody can sign in and nobody can create the first account from inside the app.
It writes rows, so it is run by hand and not through scripts/pra_deploy.py.

    python scripts/create_owner.py          # shows what would be created and writes nothing
    python scripts/create_owner.py --tulis  # asks for the details, shows the database it will write to, writes after you type "ya"

The password is asked with hidden input and stored only as a bcrypt hash; it is never printed, never kept as text and never taken from a file.
Run it against the database you mean: DATABASE_URL decides, and the host and name are shown before anything is written.
It is safe to run again: when an active owner account already exists it stops without changing anything.
"""
import getpass
import sys
import unicodedata
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import func, select  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402
from sqlalchemy.exc import IntegrityError, ProgrammingError  # noqa: E402

from app.core.clock import now, today  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.core.finance.payment_methods import seed_defaults as seed_payment_methods  # noqa: E402
from app.core.password_policy import MIN_PASSWORD_LENGTH, weakness  # noqa: E402
from app.core.security import BCRYPT_MAX_BYTES, hash_password  # noqa: E402
from app.core.settings import settings  # noqa: E402
from app.core.visitors import seed_defaults as seed_visitor_lists  # noqa: E402
from app.models.outlet import Outlet  # noqa: E402
from app.models.role import Role  # noqa: E402
from app.models.user import User  # noqa: E402
from web.management.branches.constants import DEFAULT_RADIUS_METERS, MAX_NAME_LENGTH as MAX_BRANCH_NAME_LENGTH  # noqa: E402
from web.management.users.constants import MAX_NAME_LENGTH, MAX_USERNAME_LENGTH  # noqa: E402

OWNER_ROLE_ID = "owner"
OWNER_ROLE_NAME = "Pemilik"
OWNER_ROLE_DESCRIPTION = "Pemilik: akses penuh ke semua cabang dan semua fitur."
CONFIRMATION = "ya"


def tidy(text: str) -> str:
    """A byte-order mark piped in from a shell is not part of the text; the rest is stored in the one normal form (NFC)."""
    return unicodedata.normalize("NFC", " ".join(text.replace("\ufeff", "").split()))


def ask(label: str, limit: int) -> str:
    while True:
        value = tidy(input(f"{label}: "))
        if not value:
            print("  Tidak boleh kosong.")
        elif len(value) > limit:
            print(f"  Maksimal {limit} karakter.")
        else:
            return value


def ask_username() -> str:
    while True:
        value = unicodedata.normalize("NFC", input("Username (tanpa spasi): ").replace("\ufeff", "").strip())
        if not value or " " in value:
            print("  Wajib diisi dan tidak boleh berisi spasi.")
        elif len(value) > MAX_USERNAME_LENGTH:
            print(f"  Maksimal {MAX_USERNAME_LENGTH} karakter.")
        else:
            return value


def ask_password(username: str) -> str:
    while True:
        first = getpass.getpass(f"Kata sandi (minimal {MIN_PASSWORD_LENGTH} karakter, tidak terlihat saat diketik): ")
        reason = weakness(first, username)
        if reason is not None:
            print(f"  {reason}")
        elif len(first.encode("utf-8")) > BCRYPT_MAX_BYTES:
            print(f"  Maksimal {BCRYPT_MAX_BYTES} byte; bagian di atasnya tidak ikut diperiksa saat masuk.")
        elif first.lower() == username.lower():
            print("  Kata sandi tidak boleh sama dengan username.")
        elif getpass.getpass("Ulangi kata sandi: ") != first:
            print("  Dua isian tidak sama.")
        else:
            return first


def write_owner(db, branch_name: str | None, full_name: str, username: str, password: str) -> None:
    """Menulis cabang pertama (bila diminta), peran pemilik (bila belum ada), dan akun pemiliknya; pemanggil yang melakukan commit."""
    role = db.get(Role, OWNER_ROLE_ID)
    if branch_name:
        outlet = Outlet(id=str(uuid.uuid4()), name=branch_name, is_active=True, attendance_radius_meters=DEFAULT_RADIUS_METERS)
        db.add(outlet)
        db.flush()
        seed_payment_methods(db, outlet.id)
        seed_visitor_lists(db, outlet.id)
    if role is None:
        db.add(
            Role(
                id=OWNER_ROLE_ID,
                name=OWNER_ROLE_NAME,
                description=OWNER_ROLE_DESCRIPTION,
                permissions=[],
                is_default=True,
                sort_order=0,
                is_admin=True,
                is_protected=True,
                created_at=now(),
                updated_at=now(),
            )
        )
        db.flush()
    # A full-access role works across branches, so the account is bound to none (web/management/user/service._placement).
    db.add(
        User(
            id=str(uuid.uuid4()),
            name=full_name,
            username=username,
            password_hash=hash_password(password),
            role_id=OWNER_ROLE_ID,
            outlet_id=None,
            is_active=True,
            joined_date=today(),
            created_at=now(),
        )
    )


def main() -> int:
    write = "--tulis" in sys.argv[1:]
    url = make_url(settings.database_url)
    target = f"{url.host}:{url.port}/{url.database}"

    print(f"Database: {target}")
    with SessionLocal() as db:
        try:
            existing_owner = db.scalar(select(User).where(User.role_id == OWNER_ROLE_ID, User.deleted_at.is_(None)).limit(1))
        except ProgrammingError:
            db.rollback()
            print("Tabel belum ada di database ini. Jalankan dulu: python -m alembic upgrade head. Tidak ada yang diubah.")
            return 1
        role = db.get(Role, OWNER_ROLE_ID)
        branches = db.scalar(select(func.count()).select_from(Outlet)) or 0

        if existing_owner is not None:
            print(f"Sudah ada akun pemilik aktif ({existing_owner.username}). Tidak ada yang diubah.")
            return 0
        print(f"Peran '{OWNER_ROLE_ID}': {'sudah ada' if role else 'AKAN DIBUAT'}")
        print(f"Cabang: {branches} ada" + ("" if branches else "; cabang pertama AKAN DIBUAT"))
        print("Akun pemilik: AKAN DIBUAT")
        if not write:
            print("Belum ada yang ditulis. Jalankan dengan --tulis untuk membuatnya.")
            return 0

        print()
        branch_name = ask("Nama cabang pertama", MAX_BRANCH_NAME_LENGTH) if not branches else None
        full_name = ask("Nama lengkap pemilik", MAX_NAME_LENGTH)
        username = ask_username()
        # Deleted accounts count too: their username stays taken (web/management/user/repository.username_owner).
        if db.scalar(select(User.id).where(func.lower(User.username) == username.lower())) is not None:
            print(f"Username '{username}' sudah dipakai akun lain. Tidak ada yang diubah.")
            return 1
        password = ask_password(username)

        print()
        print(f"Akan menulis ke database {target}:")
        if branch_name:
            print(f"  - cabang '{branch_name}' beserta metode bayar dan daftar pengunjung bawaannya")
        if role is None:
            print(f"  - peran '{OWNER_ROLE_ID}' ({OWNER_ROLE_NAME}), terlindungi, akses penuh")
        print(f"  - akun pemilik '{username}' ({full_name})")
        if input(f'Ketik "{CONFIRMATION}" untuk melanjutkan: ').strip().lower() != CONFIRMATION:
            print("Dibatalkan. Tidak ada yang ditulis.")
            return 1

        try:
            write_owner(db, branch_name, full_name, username, password)
            db.commit()
        except IntegrityError as error:
            db.rollback()
            print(f"Gagal: data bertabrakan dengan yang sudah ada ({error.orig.__class__.__name__}). Tidak ada yang ditulis.")
            return 1
        print("Selesai. Akun pemilik dibuat; masuk dengan username tadi.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
