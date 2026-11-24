from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.role import Role

CROSS_BRANCH_PERMISSION = "cabang.lintas"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    username: Mapped[str] = mapped_column(String(100))
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    emergency_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    emergency_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    emergency_relation: Mapped[str | None] = mapped_column(String(50), nullable=True)
    joined_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    photo_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Empty only on a deleted account, which lets go of its role so the role can still be deleted.
    role_id: Mapped[str | None] = mapped_column(String, nullable=True)
    outlet_id: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # A deleted account keeps its row so the history in its name stays whole; it no longer signs in or appears in any list.
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    role: Mapped[Role | None] = relationship(Role, primaryjoin="foreign(User.role_id) == Role.id", lazy="selectin")

    def allows(self, permission: str) -> bool:
        return self.role is not None and self.role.allows(permission)

    @property
    def working_outlet_id(self) -> str | None:
        """The one place that says where this person works; for now their placement."""
        return self.outlet_id

    @property
    def locked_outlet_id(self) -> str | None:
        """The branch that confines this person, or None when they may cross branches."""
        if self.working_outlet_id and not self.allows(CROSS_BRANCH_PERMISSION):
            return self.working_outlet_id
        return None
