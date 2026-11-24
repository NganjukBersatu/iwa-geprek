"""The pairing code a tablet types to register itself; only its hash is stored."""
import secrets

# No 0/O and 1/I/L, so the code can be typed safely from a screen.
CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 8
CODE_GROUP = 4


def new_code() -> str:
    """Shown in groups, as in K7M2-9QXA."""
    raw = "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))
    return f"{raw[:CODE_GROUP]}-{raw[CODE_GROUP:]}"


def normalise(code: str) -> str:
    """Upper case without spaces or dashes, so the way it is typed does not matter."""
    return "".join(ch for ch in code.upper() if ch.isalnum())
