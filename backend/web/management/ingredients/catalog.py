"""The shared catalog: one name and unit that every branch's row of the same ingredient follows."""
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.models.ingredient import CatalogIngredient, Ingredient
from web.management.ingredients import messages, repository
from web.management.ingredients.constants import CONFLICT


def tidy(name: str) -> str:
    """Spaces at the edges go, runs of spaces inside become one."""
    return " ".join(name.split())


def ensure(db: Session, name: str, unit_id: str) -> CatalogIngredient:
    """The entry for this name and unit, found or made; the same name with another unit is refused, since merging them would change what the stock means."""
    existing = repository.catalog_named(db, name)
    if existing is not None:
        if existing.unit_id != unit_id:
            raise DomainError(messages.unit_clash(existing.name, repository.unit_name(db, existing.unit_id) or "", repository.unit_name(db, unit_id) or unit_id), status=CONFLICT)
        return existing
    entry = CatalogIngredient(name=name, unit_id=unit_id)
    db.add(entry)
    db.flush()
    return entry


def rename(db: Session, entry: CatalogIngredient, name: str | None, unit_id: str | None) -> None:
    """Changes the entry and every linked row at once; refused, with nothing changed, when the new name collides."""
    linked = repository.linked_to(db, entry.id)
    if name is not None:
        other = repository.catalog_named(db, name)
        if other is not None and other.id != entry.id:
            raise DomainError(messages.catalog_name_taken(other.name), status=CONFLICT)
        clashing = [row for row in linked if repository.named_in_branch(db, row.outlet_id, name, except_id=row.id)]
        if clashing:
            raise DomainError(messages.branch_name_taken(name, repository.branch_names(db, [row.outlet_id for row in clashing])), status=CONFLICT)
        entry.name = name
        for row in linked:
            row.name = name
    if unit_id is not None:
        entry.unit_id = unit_id
        for row in linked:
            row.unit_id = unit_id


def clean_if_unused(db: Session, catalog_id: str | None) -> None:
    """An unused entry would keep blocking its name from another unit."""
    if catalog_id is None or repository.linked_to(db, catalog_id):
        return
    entry = repository.catalog_entry(db, catalog_id)
    if entry is not None:
        db.delete(entry)


def linked_outside(db: Session, entry: CatalogIngredient, outlet_id: str) -> bool:
    return any(row.outlet_id != outlet_id for row in repository.linked_to(db, entry.id))


def is_linked(row: Ingredient) -> bool:
    return row.catalog_id is not None
