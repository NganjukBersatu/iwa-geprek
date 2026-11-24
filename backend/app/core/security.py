"""Password and token hashing that reads and writes the same hashes the legacy service stores."""
import hashlib

import bcrypt

BCRYPT_MAX_BYTES = 72


def _prepared(password: str) -> bytes:
    """bcrypt reads only the first 72 bytes, and the legacy service did too, so longer passwords still match."""
    return password.encode("utf-8")[:BCRYPT_MAX_BYTES]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_prepared(password), bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(_prepared(password), password_hash.encode("ascii"))
    except ValueError:
        return False


def hash_token(token: str) -> str:
    """Tokens are stored only as their SHA-256, so a leaked table cannot be replayed."""
    return hashlib.sha256(token.encode()).hexdigest()
