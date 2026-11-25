"""Membuat akun pemilik pertama tanpa input, dari variabel lingkungan server, lalu selesai tanpa mengubah apa pun bila pemilik sudah ada.

    python scripts/bootstrap_owner.py

Membaca OWNER_USERNAME, OWNER_NAME (bawaan sama dengan username), dan OWNER_PASSWORD. Tidak membuat cabang; cabang dibuat pemilik di web admin.
Kata sandi tidak pernah ditulis di repositori; hapus OWNER_PASSWORD dari variabel Railway setelah akun jadi.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import func, select  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402
from scripts.create_owner import OWNER_ROLE_ID, write_owner  # noqa: E402


def main() -> int:
    username = os.environ.get("OWNER_USERNAME", "").strip()
    password = os.environ.get("OWNER_PASSWORD", "")
    name = os.environ.get("OWNER_NAME", "").strip() or username
    if not username or not password:
        print("OWNER_USERNAME dan OWNER_PASSWORD belum diisi di variabel server. Tidak ada yang diubah.")
        return 1
    with SessionLocal() as db:
        owner = db.scalar(select(User.id).where(User.role_id == OWNER_ROLE_ID, User.deleted_at.is_(None), User.is_active).limit(1))
        if owner is not None:
            print("Akun pemilik sudah ada. Tidak ada yang diubah.")
            return 0
        if db.scalar(select(User.id).where(func.lower(User.username) == username.lower())) is not None:
            print(f"Username '{username}' sudah dipakai akun lain. Tidak ada yang diubah.")
            return 1
        write_owner(db, None, name, username, password)
        db.commit()
    print(f"Akun pemilik '{username}' dibuat, tanpa cabang.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
