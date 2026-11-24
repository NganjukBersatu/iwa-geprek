from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LoginAttempt(Base):
    """Wrong passwords counted per username, so guessing one account's password is slowed down; see app.auth.attempts.

    The key is the SHA-256 of the lower-cased username: a name that does not exist counts the same as one that does (nobody can tell them
    apart), and a password typed into the username box by mistake is never stored.
    """

    __tablename__ = "login_attempts"

    username_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    # Wrong passwords inside the current window; back to 0 when the account is locked.
    failures: Mapped[int] = mapped_column(Integer)
    # Locks in a row without a quiet day between them; each one lasts twice as long as the last, up to a limit.
    lockouts: Mapped[int] = mapped_column(Integer)
    window_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
