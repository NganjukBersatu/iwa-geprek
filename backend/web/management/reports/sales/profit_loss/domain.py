"""What the profit and loss service hands to the mappers."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class ProfitLoss:
    start: date
    end: date
    revenue: Decimal
    transaction_count: int
    cost_of_goods_sold: Decimal
    cost_complete: bool
    lines_without_cost: int
    orders_without_lines: int
    revenue_without_lines: Decimal
    items_without_cost: list[str]
    gross_profit: Decimal
    gross_margin_percent: Decimal | None
    waste: Decimal
    rnd: Decimal
    count_difference: Decimal
    other_ingredient_costs: Decimal
    operating_expenses: Decimal
    ingredient_purchases: Decimal
    net_profit: Decimal
    net_margin_percent: Decimal | None
    cash_flow: Decimal
