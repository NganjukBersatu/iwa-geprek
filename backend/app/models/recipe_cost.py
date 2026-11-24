from decimal import Decimal

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

ADD_COST_PERCENT = "persen"
ADD_COST_RUPIAH = "rupiah"


class RecipeAddCost(Base):
    """Costing set by hand on one recipe at one branch; an empty field follows the branch settings."""

    __tablename__ = "recipe_add_costs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    outlet_id: Mapped[str] = mapped_column(String)
    menu_item_id: Mapped[str] = mapped_column(String)
    kind: Mapped[str | None] = mapped_column(String(10), nullable=True)
    value: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    overhead: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    target_margin_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
