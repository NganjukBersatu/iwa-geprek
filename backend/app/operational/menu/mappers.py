from app.core.http import static_url
from app.models.category import Category
from app.operational.menu.domain import MenuDetail, MenuPage, MenuView
from app.operational.menu.schemas import (
    CategoryOut,
    ExtraDetailOut,
    MenuDetailOut,
    MenuOut,
    MenuPageOut,
    RecipeLineDetailOut,
    VariantGroupDetailOut,
)


def menu_out(view: MenuView, base_url: str) -> MenuOut:
    item = view.item
    return MenuOut(
        id=item.id,
        name=item.name,
        description=item.description,
        price=view.selling_price,
        category_id=item.category_id,
        category_name=view.category_name,
        image_url=static_url(base_url, item.image_path),
        is_available=item.is_available and not view.marked_out_here,
        switched_off_for_all=not item.is_available,
        ready_to_sell=view.ready_to_sell,
        missing_ingredients=view.missing_ingredients,
        has_fixed_cost=item.fixed_cost is not None,
    )


def menu_detail_out(detail: MenuDetail, base_url: str) -> MenuDetailOut:
    return MenuDetailOut(
        menu=menu_out(detail.view, base_url),
        variant_groups=[VariantGroupDetailOut(name=group.name, required=group.required, choices=[choice.name for choice in group.choices]) for group in detail.variant_groups],
        extras=[ExtraDetailOut(name=extra.name, price=extra.price) for extra in detail.extras],
        recipe=None if detail.recipe is None else [
            RecipeLineDetailOut(ingredient_name=row.ingredient_name, unit=row.unit, qty=row.qty, stock=row.stock, short=row.stock < row.qty) for row in detail.recipe
        ],
        portions_left=detail.portions_left,
        maker_station=detail.maker_station,
        sold_today=detail.sold_today,
        cost_basis=detail.cost_basis.value,
    )


def menu_page_out(page: MenuPage, base_url: str) -> MenuPageOut:
    return MenuPageOut(
        items=[menu_out(view, base_url) for view in page.items], total=page.total, page=page.page, size=page.size
    )


def category_out(category: Category) -> CategoryOut:
    return CategoryOut(id=category.id, name=category.name)
