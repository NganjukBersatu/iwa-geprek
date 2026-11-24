"""Satu pintu aturan kata sandi: panjang minimal dan kelemahan yang ditolak, dipakai profil, pembuatan karyawan, dan skrip."""
import re

from app.core import brand, messages
from app.core.errors import DomainError

# Tanpa MFA, panjang minimal 15 karakter; tidak ada aturan campuran jenis karakter dan tidak ada pergantian berkala.
MIN_PASSWORD_LENGTH = 15
MAX_PASSWORD_LENGTH = 128

# Kata sandi dengan lebih sedikit karakter berbeda daripada ini hampir pasti pengulangan.
MIN_DISTINCT_CHARACTERS = 6
# Nama pengguna lebih pendek dari ini tidak diperiksa, karena hampir pasti muncul sebagai kebetulan.
MIN_USERNAME_LENGTH_CHECKED = 4

# Dasar kata sandi yang paling umum dan nama layanan ini, dibandingkan setelah angka dan simbol dibuang.
COMMON_BASES = frozenset(
    {
        "password",
        "passw",
        "katasandi",
        "sandi",
        "qwerty",
        "qwertyuiop",
        "asdfghjkl",
        "zxcvbnm",
        "iloveyou",
        "letmein",
        "welcome",
        "admin",
        "administrator",
        brand.SLUG,
        brand.NAME.replace(" ", "").lower(),
    }
)

_NON_LETTERS = re.compile(r"[^a-z]")


# Urutan huruf dan angka diulang supaya urutan yang melingkar (9 ke 0, z ke a) ikut terdeteksi.
_SEQUENCES = ("abcdefghijklmnopqrstuvwxyz" * 2, "0123456789" * 4)


def _is_run(password: str) -> bool:
    """Seluruhnya urutan naik atau turun, seperti 123456789012345 atau abcdefghijklmnop."""
    return any(password in sequence or password in sequence[::-1] for sequence in _SEQUENCES)


def weakness(password: str, username: str) -> str | None:
    """Kalimat penolakan untuk kata sandi yang terlalu lemah, atau None bila diterima."""
    if len(password) < MIN_PASSWORD_LENGTH:
        return messages.PASSWORD_TOO_SHORT.format(minimum=MIN_PASSWORD_LENGTH)
    lowered = password.lower()
    if len(set(lowered)) < MIN_DISTINCT_CHARACTERS or _is_run(lowered):
        return messages.PASSWORD_TOO_REPETITIVE
    name = username.strip().lower()
    if len(name) >= MIN_USERNAME_LENGTH_CHECKED and name in lowered:
        return messages.PASSWORD_HAS_USERNAME
    if _NON_LETTERS.sub("", lowered) in COMMON_BASES:
        return messages.PASSWORD_TOO_COMMON
    return None


def ensure_acceptable(password: str, username: str, field: str) -> None:
    """Menolak kata sandi yang terlalu lemah; [field] adalah nama isian di permintaan, supaya pesannya muncul di isian itu."""
    reason = weakness(password, username)
    if reason is not None:
        raise DomainError(reason, field=field)
