"""Builds the profit and loss report; figures and rounding match the legacy /laporan routes exactly."""
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.ingredient import INGREDIENT_RND, INGREDIENT_WASTE
from web.management.reports.common import CENT, from_today, optional_percent
from web.management.reports.sales.profit_loss import repository
from web.management.reports.sales.profit_loss.domain import ProfitLoss


def profit_loss(db: Session, start: date | None, end: date | None, outlet_id: str | None) -> ProfitLoss:
    """Ingredients become cost when sold through recipes, so purchases are kept out of operating expenses."""
    start, end = from_today(start, end)

    revenue, transaction_count = repository.revenue_and_count(db, start, end, outlet_id)
    cost, lines, costed = repository.cost_of_goods(db, start, end, outlet_id)
    empty_orders, empty_revenue = repository.orders_without_lines(db, start, end, outlet_id)
    gross_profit = revenue - cost

    losses = repository.ingredient_losses(db, start, end, outlet_id)
    waste = Decimal(str(losses.get(INGREDIENT_WASTE) or 0)).quantize(CENT)
    rnd = Decimal(str(losses.get(INGREDIENT_RND) or 0)).quantize(CENT)
    difference = repository.count_difference(db, start, end, outlet_id).quantize(CENT)
    other_ingredient_costs = waste + rnd + difference

    operating, purchases = repository.split_expenses(db, start, end, outlet_id)
    net_profit = gross_profit - other_ingredient_costs - operating

    return ProfitLoss(
        start=start,
        end=end,
        revenue=revenue,
        transaction_count=transaction_count,
        cost_of_goods_sold=cost.quantize(CENT),
        cost_complete=costed == lines and empty_orders == 0,
        lines_without_cost=lines - costed,
        orders_without_lines=empty_orders,
        revenue_without_lines=empty_revenue,
        items_without_cost=repository.items_without_cost(db, start, end, outlet_id),
        gross_profit=gross_profit,
        gross_margin_percent=optional_percent(gross_profit, revenue),
        waste=waste,
        rnd=rnd,
        count_difference=difference,
        other_ingredient_costs=other_ingredient_costs,
        operating_expenses=operating,
        ingredient_purchases=purchases,
        net_profit=net_profit,
        net_margin_percent=optional_percent(net_profit, revenue),
        cash_flow=revenue - operating - purchases,
    )
