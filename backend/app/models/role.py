from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text, false
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# These two roles always hold every permission, including ones added to the catalog later.
FULL_ACCESS_ROLE_IDS = frozenset({"owner", "admin"})


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String(60))
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    permissions: Mapped[list] = mapped_column(JSON)
    # A default role cannot be deleted, so a branch always has one to register people with.
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    # Orders the list only; roles are never ranked against each other.
    sort_order: Mapped[int] = mapped_column(Integer, default=100)
    # A supervising role; a self-made schedule cannot pick it.
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    is_protected: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    # Stasiun yang tampil di tablet untuk akun berperan ini; kosong berarti tanpa stasiun.
    station_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    # The account that made the role; empty for roles that predate this column. A protected role can still be changed by its creator.
    created_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @property
    def has_full_access(self) -> bool:
        return self.id in FULL_ACCESS_ROLE_IDS

    def allows(self, permission: str) -> bool:
        return self.has_full_access or permission in (self.permissions or [])
