from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.auth import passes
from app.core.catalog import menu as catalog_menu
from app.core.catalog import availability, recipe_book, selling
from app.core.clock import today
from app.core.orders import lines as line_rules
from app.core.orders import recipes as menu_recipes
from app.core.orders import station_setup
from app.models.user import User
from app.core.pricing import price_map
from app.core.uploads import UploadedFile
from app.models.menu_item import MenuItem
from app.core.errors import DomainError
from app.operational.menu import messages, repository
from app.operational.menu.domain import CostBasis, MenuDetail, MenuPage, MenuView, RecipeStock
from app.operational.menu.upload import RULE


def _views(db: Session, outlet_id: str | None, rows: list[tuple[MenuItem, str | None]]) -> list[MenuView]:
    ids = [item.id for item, _ in rows]
    prices = price_map(db, outlet_id, [item for item, _ in rows])
    ready = line_rules.ready_ids(db, outlet_id, ids)
    missing = line_rules.missing_ingredients(db, outlet_id, ids)
    marked_out = availability.off_ids(db, outlet_id, ids)
    return [
        MenuView(
            item=item,
            selling_price=prices[item.id],
            category_name=name,
            ready_to_sell=item.id in ready,
            marked_out_here=item.id in marked_out,
            missing_ingredients=missing.get(item.id, []),
        )
        for item, name in rows
    ]


def _view(db: Session, outlet_id: str | None, item: MenuItem) -> MenuView:
    return _views(db, outlet_id, [(item, repository.category_name(db, item.category_id))])[0]


def detail(db: Session, user: User, outlet_id: str, menu_id: str) -> MenuDetail:
    """Semua yang dibutuhkan halaman rincian satu menu di tablet, dalam jumlah query tetap."""
    item = catalog_menu.existing(db, menu_id)
    if not line_rules.is_sold_at(item, outlet_id):
        raise DomainError(catalog_menu.MENU_NOT_FOUND, status=catalog_menu.NOT_FOUND)
    view = _view(db, outlet_id, item)
    sellable = next(iter(selling.menus_of(db, outlet_id, only={menu_id})), None)
    maker = station_setup.setup_of(db, outlet_id).maker(station_setup.makers_of_menus(db, outlet_id, {menu_id}).get(menu_id))
    lines = sorted(menu_recipes.of_menus(db, outlet_id, [menu_id]).get(menu_id, []), key=lambda line: line.ingredient_name.lower())
    recipe: list[RecipeStock] | None = None
    portions: int | None = None
    if passes(user, recipe_book.READ_GATE):
        ids = {line.ingredient_id for line in lines}
        units = recipe_book.units_of(db, ids)
        stock = repository.balances(db, outlet_id, ids)
        recipe = [RecipeStock(line.ingredient_name, units.get(line.ingredient_id), line.qty, stock.get(line.ingredient_id, Decimal(0))) for line in lines]
        # Bahan yang stoknya minus dihitung nol, karena porsi tidak bisa dibuat dari stok yang tidak ada.
        portions = min((int(max(row.stock, Decimal(0)) // row.qty) for row in recipe), default=None)
    return MenuDetail(
        view=view,
        variant_groups=sellable.variant_groups if sellable else [],
        extras=sellable.extras if sellable else [],
        recipe=recipe,
        portions_left=portions,
        maker_station=maker.station.name if maker else None,
        sold_today=repository.sold_on(db, outlet_id, menu_id, today()),
        cost_basis=_cost_basis(db, outlet_id, item, bool(lines)),
    )


def _cost_basis(db: Session, outlet_id: str, item: MenuItem, has_recipe: bool) -> CostBasis:
    # Ketiganya saling meniadakan (dijaga app.core.catalog.fixed_cost), jadi urutan pemeriksaan tidak mengubah hasil.
    if item.fixed_cost is not None:
        return CostBasis.FIXED
    if has_recipe:
        return CostBasis.RECIPE
    if repository.is_resale(db, outlet_id, item.id):
        return CostBasis.RESALE
    return CostBasis.NONE


def page_of(
    db: Session, outlet_id: str, search: str | None, category_id: str | None, page: int, size: int, sort: str | None = None
) -> MenuPage:
    rows, total = repository.page_of(db, outlet_id, (search or "").strip() or None, category_id, page, size, sort)
    return MenuPage(items=_views(db, outlet_id, rows), total=total, page=page, size=size)


def update(db: Session, outlet_id: str | None, menu_id: str, changes: dict) -> MenuView:
    """Only the fields that were sent change; the price is set from the management web only."""
    item = catalog_menu.existing(db, menu_id)
    if "name" in changes:
        item.name = catalog_menu.clean_name(changes["name"])
    if "description" in changes:
        item.description = catalog_menu.clean_description(changes["description"])
    if "category_id" in changes:
        item.category_id = catalog_menu.checked_category(db, changes["category_id"])
    if "is_available" in changes and changes["is_available"] is not None:
        item.is_available = changes["is_available"]
    db.commit()
    db.refresh(item)
    return _view(db, outlet_id, item)


def set_available(db: Session, user: User, outlet_id: str, menu_id: str, available: bool) -> MenuView:
    """Marks the menu out, or on again, at this branch only; what the web switched off for every branch stays off."""
    item = catalog_menu.existing(db, menu_id)
    if not line_rules.is_sold_at(item, outlet_id):
        raise DomainError(line_rules.MENU_NOT_SOLD.format(menu=item.name))
    if available and not item.is_available:
        raise DomainError(messages.SWITCHED_OFF_FOR_ALL.format(menu=item.name))
    availability.mark(db, user.id, outlet_id, menu_id, available)
    db.commit()
    return _view(db, outlet_id, item)


def delete(db: Session, menu_id: str) -> None:
    catalog_menu.delete(db, menu_id)


def set_photo(db: Session, outlet_id: str | None, menu_id: str, image: UploadedFile) -> MenuView:
    return _view(db, outlet_id, catalog_menu.set_photo(db, menu_id, image, RULE))
