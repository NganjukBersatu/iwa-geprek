"""Membuat akun pemilik pertama tanpa input, dari variabel server, lalu selesai tanpa mengubah apa pun bila pemilik sudah ada.

    python scripts/bootstrap_owner.py

Membaca OWNER_USERNAME, OWNER_NAME (bawaan sama dengan username), OWNER_PASSWORD_HASH_B64, dan OWNER_BRANCH (nama cabang pertama, boleh kosong).
Kata sandi tidak pernah sampai ke server: hash-nya dibuat di komputer sendiri dengan python scripts/create_owner_remote.py --hash-saja.
Cabang hanya dibuat bila belum ada cabang sama sekali, tanpa data contoh. Hapus variabel OWNER_* dari Railway setelah akun jadi.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import func, select  # noqa: E402
from sqlalchemy.exc import IntegrityError, ProgrammingError  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.models.outlet import Outlet  # noqa: E402
from app.models.user import User  # noqa: E402
from scripts.create_owner import (  # noqa: E402
    HASH_VARIABLE,
    MAX_BRANCH_NAME_LENGTH,
    MAX_NAME_LENGTH,
    OWNER_ROLE_ID,
    clean_username,
    hash_from_environment,
    text_problem,
    tidy,
    username_problem,
    write_owner,
)


def main() -> int:
    username = clean_username(os.environ.get("OWNER_USERNAME", ""))
    name = tidy(os.environ.get("OWNER_NAME", "")) or username
    branch = tidy(os.environ.get("OWNER_BRANCH", "")) or None
    password_hash = hash_from_environment()
    if not username or password_hash is None:
        print(f"OWNER_USERNAME dan {HASH_VARIABLE} belum diisi di variabel server. Tidak ada yang diubah.")
        return 1
    problems = [
        (label, problem)
        for label, problem in (
            ("OWNER_USERNAME", username_problem(username)),
            ("OWNER_NAME", text_problem(name, MAX_NAME_LENGTH)),
            ("OWNER_BRANCH", text_problem(branch, MAX_BRANCH_NAME_LENGTH) if branch else None),
        )
        if problem is not None
    ]
    if problems:
        for label, problem in problems:
            print(f"{label}: {problem}")
        print("Tidak ada yang diubah.")
        return 1
    with SessionLocal() as db:
        try:
            owner = db.scalar(select(User.id).where(User.role_id == OWNER_ROLE_ID, User.deleted_at.is_(None)).limit(1))
        except ProgrammingError:
            db.rollback()
            print("Tabel belum ada di database ini. Jalankan dulu: python -m alembic upgrade head. Tidak ada yang diubah.")
            return 1
        if owner is not None:
            print("Akun pemilik sudah ada. Tidak ada yang diubah.")
            return 0
        # Deleted accounts count too: their username stays taken (web/management/user/repository.username_owner).
        if db.scalar(select(User.id).where(func.lower(User.username) == username.lower())) is not None:
            print(f"Username '{username}' sudah dipakai akun lain. Tidak ada yang diubah.")
            return 1
        if branch and db.scalar(select(Outlet.id).limit(1)) is not None:
            print(f"Cabang sudah ada, jadi OWNER_BRANCH '{branch}' tidak dibuat.")
            branch = None
        try:
            write_owner(db, branch, name, username, "", password_hash)
            db.commit()
        except IntegrityError as error:
            db.rollback()
            print(f"Gagal: data bertabrakan dengan yang sudah ada ({error.orig.__class__.__name__}). Tidak ada yang ditulis.")
            return 1
    print(f"Akun pemilik '{username}' dibuat" + (f", dengan cabang '{branch}'." if branch else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
