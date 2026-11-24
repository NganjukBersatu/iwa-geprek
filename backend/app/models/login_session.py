from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LoginSession(Base):
    """One sign-in on one device; its token is valid only while this row is neither revoked nor past its end."""

    __tablename__ = "login_sessions"
    __table_args__ = (Index("ix_login_sessions_user", "user_id"),)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"))
    # "cookie" for a browser, "bearer" for the tablet and other callers that send the token themselves.
    channel: Mapped[str] = mapped_column(String(16))
    device_label: Mapped[str | None] = mapped_column(String(160), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    # Written at most once a minute; a browser sign-in idle for session_idle_minutes after this is refused.
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
