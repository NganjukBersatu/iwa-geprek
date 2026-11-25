"""Membuat akun pemilik pertama di server Railway dari komputer sendiri:

    python scripts/create_owner_remote.py

Kata sandi diketik tersembunyi di komputer ini, karena ketikan tersembunyi lewat railway ssh dari Windows selalu terbaca kosong.
Yang dikirim ke server hanya hash bcrypt-nya; sisanya (nama cabang, nama, username, konfirmasi "ya") ditanyakan oleh
scripts/create_owner.py di server seperti biasa.
"""
import base64
import getpass
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.password_policy import MIN_PASSWORD_LENGTH, weakness  # noqa: E402
from app.core.security import BCRYPT_MAX_BYTES, hash_password  # noqa: E402

SERVICE = "backend"
HASH_VARIABLE = "OWNER_PASSWORD_HASH_B64"


def ask_password(username: str) -> str:
    while True:
        first = getpass.getpass(f"Kata sandi (minimal {MIN_PASSWORD_LENGTH} karakter, tidak terlihat saat diketik): ")
        reason = weakness(first, username)
        if reason is not None:
            print(f"  {reason}")
        elif len(first.encode("utf-8")) > BCRYPT_MAX_BYTES:
            print(f"  Maksimal {BCRYPT_MAX_BYTES} byte; bagian di atasnya tidak ikut diperiksa saat masuk.")
        elif getpass.getpass("Ulangi kata sandi: ") != first:
            print("  Dua isian tidak sama.")
        else:
            return first


def main() -> int:
    railway = shutil.which("railway.cmd") or shutil.which("railway")
    if railway is None:
        print("Railway CLI belum terpasang. Jalankan dulu: npm install -g @railway/cli, lalu railway login.")
        return 1
    username = input("Username yang akan dipakai (tanpa spasi, sama dengan yang nanti ditanyakan server): ").strip()
    encoded = base64.b64encode(hash_password(ask_password(username)).encode("ascii")).decode("ascii")
    print("Kata sandi sudah diubah menjadi hash. Sekarang server menanyakan nama cabang, nama, dan username.")
    remote = f"{HASH_VARIABLE}={encoded} python scripts/create_owner.py --tulis"
    return subprocess.run([railway, "ssh", "--service", SERVICE, "--", "sh", "-c", remote], check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
