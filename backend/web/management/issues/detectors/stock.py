"""Stock and ingredients: levels, counts beyond tolerance, purchase prices, and ingredients that need tidying."""
from datetime import timedelta
from decimal import Decimal

from sqlalchemy import and_, case, exists, func, or_, select

from app.core.money import decimal_of
from app.models.extra import ExtraRecipe
from app.models.ingredient import INGREDIENT_IN, REQUEST_PENDING, Ingredient, IngredientCard, IngredientCount, IngredientCountLine, IngredientCountRequest, RecipeIngredient
from app.models.menu_item import MenuItem
from app.models.stock import StockItem
from app.models.variant import VariantChoiceRecipe
from app.core.ingredients.openings import missing_counts as openings_missing_of
from web.management.issues import constants as c
from web.management.issues.domain import Issue, IssueKind, IssueLevel, Scope
from web.management.reports.common import CENT
from web.management.reports.inventory.low_stock import repository as low_stock
from web.management.reports.inventory.low_stock.domain import LOW_STOCK_WINDOW_DAYS, LowStockKind, LowStockLevel
from web.management.reports.inventory.low_stock.service import low_stock_item

PERCENT = 100


def stock_levels(scope: Scope) -> list[Issue]:
    """The same rule as the low stock report. amount: balance, compared: minimum, days: days until empty at the recent pace."""
    window = low_stock.usage_window(LOW_STOCK_WINDOW_DAYS)
    inside = set(scope.outlet_ids)
    issues: list[Issue] = []

    def add(outlet_id: str, balance: Decimal, minimum: Decimal, used: Decimal, kind: LowStockKind, item_id: str, name: str, unit: str | None) -> None:
        item = low_stock_item(balance, minimum, used / LOW_STOCK_WINDOW_DAYS, kind=kind, id=item_id, name=name, category=None, unit=unit or "")
        if item is None:
            return
        if item.level == LowStockLevel.OUT:
            issue_kind, level = (IssueKind.STOCK_NEGATIVE, IssueLevel.PROBLEM) if balance < 0 else (IssueKind.STOCK_OUT, IssueLevel.PROBLEM)
        else:
            issue_kind, level = IssueKind.STOCK_LOW, IssueLevel.WARNING
        issues.append(
            Issue(issue_kind, level, outlet_id, item_id, name, subject_kind=kind.value, amount=item.balance, compared=item.minimum, unit=item.unit, days=item.days_until_empty)
        )

    usage = low_stock.ingredient_usage_in(scope.db, scope.outlet_id, window)
    for ingredient, _category, unit, balance in low_stock.active_ingredient_balances(scope.db, scope.outlet_id):
        if ingredient.outlet_id in inside:
            add(ingredient.outlet_id, decimal_of(balance), decimal_of(ingredient.minimum), decimal_of(usage.get(ingredient.id, 0)), LowStockKind.INGREDIENT, ingredient.id, ingredient.name, unit)
    sold = low_stock.stock_usage_in(scope.db, scope.outlet_id, window)
    for stock, menu_name, _category, unit, balance in low_stock.tracked_stock_balances(scope.db, scope.outlet_id):
        if stock.outlet_id in inside:
            add(stock.outlet_id, decimal_of(balance), decimal_of(stock.minimum), decimal_of(sold.get(stock.menu_item_id, 0)), LowStockKind.RESALE, stock.menu_item_id, menu_name, unit)
    return issues


def counts_over_tolerance(scope: Scope) -> list[Issue]:
    """Counts closed in the last days, by the rule of the ingredient stock report. One per count; count: ingredients beyond tolerance, day: end of the period."""
    line, count, card = IngredientCountLine, IngredientCount, IngredientCard
    # Only the cards since the period began are read: the opening stock is today's balance minus everything that moved since.
    moved_since = func.coalesce(func.sum(card.qty), 0)
    purchased = func.coalesce(
        func.sum(case((and_(card.kind == INGREDIENT_IN, card.count_id.is_(None), card.business_day <= count.period_end), card.qty), else_=0)),
        0,
    )
    rows = scope.db.execute(
        select(count.id, count.outlet_id, count.period_end, line.book_balance, line.counted, line.shrink_tolerance, Ingredient.balance - moved_since, purchased)
        .join(count, count.id == line.count_id)
        .join(Ingredient, Ingredient.id == line.ingredient_id)
        .outerjoin(card, and_(card.ingredient_id == line.ingredient_id, card.outlet_id == count.outlet_id, card.business_day >= count.period_start))
        .where(count.outlet_id.in_(scope.outlet_ids), count.created_at >= scope.since(c.EVENT_DAYS))
        .group_by(line.id, count.id, count.outlet_id, count.period_end, line.book_balance, line.counted, line.shrink_tolerance, Ingredient.balance)
    ).all()
    over: dict[str, Issue] = {}
    for count_id, outlet_id, period_end, book, counted, tolerance, opening_qty, purchased_qty in rows:
        book, available = decimal_of(book), decimal_of(opening_qty) + decimal_of(purchased_qty)
        # A negative book balance is a wrong recipe or a missed purchase, which the stock levels report instead.
        if book < 0 or available <= 0:
            continue
        if ((book - decimal_of(counted)) / available * PERCENT).quantize(CENT) <= decimal_of(tolerance):
            continue
        found = over.get(count_id)
        over[count_id] = Issue(IssueKind.COUNT_OVER_TOLERANCE, IssueLevel.WARNING, outlet_id, count_id, "", day=period_end, count=(found.count or 0) + 1 if found else 1)
    return list(over.values())


def count_requests_waiting(scope: Scope) -> list[Issue]:
    """One per branch. count: requests waiting."""
    rows = scope.db.execute(
        select(IngredientCountRequest.outlet_id, func.count(IngredientCountRequest.id))
        .where(IngredientCountRequest.status == REQUEST_PENDING, IngredientCountRequest.outlet_id.in_(scope.outlet_ids))
        .group_by(IngredientCountRequest.outlet_id)
    ).all()
    return [Issue(IssueKind.COUNT_REQUEST_WAITING, IssueLevel.NOTICE, outlet_id, None, "", count=count) for outlet_id, count in rows]


def openings_missing(scope: Scope) -> list[Issue]:
    """Satu per cabang yang masih punya bahan aktif tanpa stok awal di periode berjalan. count: bahan yang belum diisi, day: hari pertama periode."""
    return [
        Issue(IssueKind.OPENING_MISSING, IssueLevel.WARNING, outlet_id, None, "", day=start, count=count)
        for outlet_id, (start, count) in openings_missing_of(scope.db, scope.outlet_ids).items()
        if count > 0
    ]


def purchase_price_jumps(scope: Scope) -> list[Issue]:
    """A recent purchase priced well above the one before it of the same ingredient. amount: new unit price, compared: previous, percent: the rise."""
    card = IngredientCard
    previous = func.lag(card.unit_price).over(partition_by=card.ingredient_id, order_by=(card.business_day, card.created_at, card.id))
    purchases = (
        select(card.id, card.outlet_id, card.ingredient_id, card.ingredient_name, card.unit_price, card.created_at, card.business_day, previous.label("previous"))
        .where(card.kind == INGREDIENT_IN, card.unit_price > 0, card.ingredient_id.is_not(None), card.outlet_id.in_(scope.outlet_ids))
        .subquery()
    )
    rows = scope.db.execute(
        select(purchases.c.outlet_id, purchases.c.ingredient_id, purchases.c.ingredient_name, purchases.c.unit_price, purchases.c.previous, purchases.c.created_at).where(
            purchases.c.business_day >= scope.first_day(c.EVENT_DAYS),
            purchases.c.previous > 0,
            purchases.c.unit_price * PERCENT >= purchases.c.previous * (PERCENT + c.PRICE_JUMP_PERCENT),
        )
    ).all()
    return [
        Issue(
            IssueKind.PURCHASE_PRICE_JUMP,
            IssueLevel.WARNING,
            outlet_id,
            ingredient_id,
            name,
            at=at,
            amount=decimal_of(price),
            compared=decimal_of(before),
            percent=((decimal_of(price) - decimal_of(before)) / decimal_of(before) * PERCENT).quantize(CENT),
        )
        for outlet_id, ingredient_id, name, price, before, at in rows
    ]


def _active_ingredients(scope: Scope):
    return select(Ingredient.outlet_id, Ingredient.id, Ingredient.name).where(Ingredient.is_active.is_(True), Ingredient.outlet_id.in_(scope.outlet_ids))


def idle_ingredients(scope: Scope) -> list[Issue]:
    since = scope.now - timedelta(days=c.IDLE_INGREDIENT_DAYS)
    moved = exists().where(IngredientCard.ingredient_id == Ingredient.id, IngredientCard.business_day >= scope.first_day(c.IDLE_INGREDIENT_DAYS))
    rows = scope.db.execute(_active_ingredients(scope).where(Ingredient.created_at < since, ~moved)).all()
    return [Issue(IssueKind.INGREDIENT_IDLE, IssueLevel.SUGGESTION, outlet_id, ingredient_id, name) for outlet_id, ingredient_id, name in rows]


def without_minimum(scope: Scope) -> list[Issue]:
    """Ingredients and tracked resold items whose minimum is zero, so they are never reported low before they run out."""
    ingredients = [(*row, LowStockKind.INGREDIENT) for row in scope.db.execute(_active_ingredients(scope).where(Ingredient.minimum <= 0)).all()]
    resold = [
        (*row, LowStockKind.RESALE)
        for row in scope.db.execute(
            select(StockItem.outlet_id, StockItem.menu_item_id, MenuItem.name)
            .join(MenuItem, MenuItem.id == StockItem.menu_item_id)
            .where(StockItem.is_tracked.is_(True), StockItem.minimum <= 0, StockItem.outlet_id.in_(scope.outlet_ids))
        ).all()
    ]
    return [
        Issue(IssueKind.INGREDIENT_NO_MINIMUM, IssueLevel.SUGGESTION, outlet_id, item_id, name, subject_kind=kind.value)
        for outlet_id, item_id, name, kind in [*ingredients, *resold]
    ]


def unused_ingredients(scope: Scope) -> list[Issue]:
    """In no recipe of a menu, a variant choice or an extra."""
    used = or_(
        exists().where(RecipeIngredient.ingredient_id == Ingredient.id),
        exists().where(VariantChoiceRecipe.ingredient_id == Ingredient.id),
        exists().where(ExtraRecipe.ingredient_id == Ingredient.id),
    )
    rows = scope.db.execute(_active_ingredients(scope).where(~used)).all()
    return [Issue(IssueKind.INGREDIENT_UNUSED, IssueLevel.SUGGESTION, outlet_id, ingredient_id, name) for outlet_id, ingredient_id, name in rows]
