"""The menu screen of the management web; every rule about a menu lives in app.core.catalog.menu."""
import uuid

from sqlalchemy.orm import Session

from app.core.catalog import menu as catalog_menu
from app.models.menu_item import MenuItem
from web.management.menu.schemas import MenuCreateIn


def create(db: Session, body: MenuCreateIn) -> MenuItem:
    item = MenuItem(
        id=str(uuid.uuid4()),
        name=catalog_menu.clean_name(body.name),
        description=catalog_menu.clean_description(body.description),
        price=body.price,
        category_id=catalog_menu.checked_category(db, body.category_id),
        image_path=None,
        is_available=body.is_available,
        outlet_ids=catalog_menu.checked_branches(db, body.outlet_ids),
        tax_percent=body.tax_percent,
        service_percent=body.service_percent,
    )
    db.add(item)
    db.flush()
    catalog_menu.save_branch_prices(db, item, body.branch_prices)
    db.commit()
    db.refresh(item)
    return item


def update(db: Session, menu_id: str, changes: dict) -> MenuItem:
    """Only the fields that were sent change; `outlet_ids` sent empty sells the menu everywhere again."""
    item = catalog_menu.existing(db, menu_id)
    if "name" in changes:
        item.name = catalog_menu.clean_name(changes["name"])
    if "description" in changes:
        item.description = catalog_menu.clean_description(changes["description"])
    if "price" in changes and changes["price"] is not None:
        item.price = changes["price"]
    if "category_id" in changes:
        item.category_id = catalog_menu.checked_category(db, changes["category_id"])
    if "is_available" in changes and changes["is_available"] is not None:
        item.is_available = changes["is_available"]
    if "outlet_ids" in changes:
        item.outlet_ids = catalog_menu.checked_branches(db, changes["outlet_ids"])
    if "tax_percent" in changes:
        item.tax_percent = changes["tax_percent"]
    if "service_percent" in changes:
        item.service_percent = changes["service_percent"]
    catalog_menu.save_branch_prices(db, item, changes.get("branch_prices"))
    db.commit()
    db.refresh(item)
    return item
