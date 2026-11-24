"""Ingredients of a branch: the master data, its photo and its removal."""
import uuid
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import uploads
from app.core.errors import DomainError
from app.models.ingredient import CatalogIngredient, Ingredient
from app.models.user import User
from app.core.uploads import UploadedFile, UploadRule
from web.management.ingredients import catalog, messages, repository
from web.management.ingredients.constants import CONFLICT, FORBIDDEN, NOT_FOUND, PHOTO_FOLDER, UNIT_PRICE_PLACES
from web.management.ingredients.domain import IngredientDraft
from web.management.ingredients.mappers import ingredient_out
from web.management.ingredients.schemas import IngredientOut
from app.models.category import Category, Unit

UPDATABLE = ("package_price", "package_size", "unit_price", "shrink_tolerance", "minimum", "is_active", "is_available", "is_indirect")


def get(db: Session, outlet_id: str | None, ingredient_id: str) -> Ingredient:
    row = repository.find(db, ingredient_id)
    if row is None or (outlet_id and row.outlet_id != outlet_id):
        raise DomainError(messages.NOT_FOUND, status=NOT_FOUND)
    return row


def create(db: Session, outlet_id: str, draft: IngredientDraft) -> Ingredient:
    name = catalog.tidy(draft.name)
    if not name:
        raise DomainError(messages.NAME_REQUIRED)
    if repository.named_in_branch(db, outlet_id, name):
        raise DomainError(messages.already_in_branch(name), status=CONFLICT)
    _check_unit(db, draft.unit_id)
    _check_category(db, draft.category_id)
    entry = catalog.ensure(db, name, draft.unit_id)
    if repository.linked_in_branch(db, outlet_id, entry.id):
        raise DomainError(messages.already_in_branch(entry.name), status=CONFLICT)
    row = _new_row(outlet_id, entry, draft)
    db.add(row)
    db.commit()
    return row


def _new_row(outlet_id: str, entry: CatalogIngredient, draft: IngredientDraft) -> Ingredient:
    """Name and unit come from the catalog entry, not from the draft, so the same ingredient is spelled alike in every branch."""
    return Ingredient(
        outlet_id=outlet_id,
        catalog_id=entry.id,
        name=entry.name,
        category_id=draft.category_id or None,
        unit_id=entry.unit_id,
        package_price=draft.package_price,
        package_size=draft.package_size,
        unit_price=draft.unit_price if draft.unit_price is not None else _starting_unit_price(draft.package_price, draft.package_size),
        shrink_tolerance=draft.shrink_tolerance,
        minimum=draft.minimum,
        is_indirect=draft.is_indirect,
        is_active=True,
        is_available=True,
    )


def create_everywhere(db: Session, admin: User, draft: IngredientDraft) -> tuple[list[Ingredient], list[str]]:
    """The same ingredient in every active branch, so the owner does not type it per branch; a branch that already has it is skipped and named, not failed.

    An older ingredient of the same name and unit that is not linked yet is linked on the way, so a recipe can later be applied there without a twin being made.
    """
    if admin.locked_outlet_id:
        raise DomainError(messages.OWNER_ONLY)
    name = catalog.tidy(draft.name)
    if not name:
        raise DomainError(messages.NAME_REQUIRED)
    outlets = repository.active_outlets(db)
    if not outlets:
        raise DomainError(messages.NO_ACTIVE_BRANCH)
    _check_unit(db, draft.unit_id)
    _check_category(db, draft.category_id)
    entry = catalog.ensure(db, name, draft.unit_id)
    existing = repository.in_branches_named(db, [outlet.id for outlet in outlets], entry)
    linked = {row.outlet_id for row in existing if row.catalog_id == entry.id}
    taken: set[str] = set()
    for row in existing:
        taken.add(row.outlet_id)
        if row.catalog_id is None and row.outlet_id not in linked and row.unit_id == entry.unit_id:
            row.catalog_id = entry.id
            linked.add(row.outlet_id)
    created: list[Ingredient] = []
    skipped: list[str] = []
    for outlet in outlets:
        if outlet.id in taken:
            skipped.append(outlet.name)
            continue
        row = _new_row(outlet.id, entry, draft)
        db.add(row)
        created.append(row)
    db.commit()
    return created, skipped


def link_to_catalog(db: Session, admin: User, ingredient_id: str, catalog_id: str | None, create_new: bool) -> Ingredient:
    """An unlinked ingredient takes the name and unit of a catalog entry; the unit must already match, since the same name with another unit is not the same ingredient."""
    row = get(db, admin.locked_outlet_id, ingredient_id)
    if row.catalog_id:
        raise DomainError(messages.ALREADY_LINKED, status=CONFLICT)
    if bool(catalog_id) == create_new:
        raise DomainError(messages.PICK_ONE_ENTRY)
    if create_new:
        entry = catalog.ensure(db, row.name, row.unit_id)
    else:
        entry = repository.catalog_entry(db, catalog_id)
        if entry is None:
            raise DomainError(messages.CATALOG_NOT_FOUND, status=NOT_FOUND)
        if entry.unit_id != row.unit_id:
            raise DomainError(messages.link_unit_clash(row.name, repository.unit_name(db, row.unit_id) or "", entry.name, repository.unit_name(db, entry.unit_id) or ""), status=CONFLICT)
    if repository.linked_in_branch(db, row.outlet_id, entry.id) is not None:
        raise DomainError(messages.branch_has_entry(entry.name), status=CONFLICT)
    if repository.named_in_branch(db, row.outlet_id, entry.name, except_id=row.id) is not None:
        raise DomainError(messages.already_in_branch(entry.name), status=CONFLICT)
    row.catalog_id = entry.id
    row.name = entry.name
    row.unit_id = entry.unit_id
    db.commit()
    return row


def catalog_entries(db: Session) -> list[tuple[CatalogIngredient, str | None, int]]:
    counts = repository.branch_counts(db)
    units = repository.names_of(db, {entry.unit_id for entry in repository.all_catalog(db)}, Unit)
    return [(entry, units.get(entry.unit_id), counts.get(entry.id, 0)) for entry in repository.all_catalog(db)]


def delete_catalog_entry(db: Session, catalog_id: str) -> None:
    """Refused while any ingredient is linked; an entry nobody uses is leftover that is worth cleaning."""
    entry = repository.catalog_entry(db, catalog_id)
    if entry is None:
        raise DomainError(messages.CATALOG_NOT_FOUND, status=NOT_FOUND)
    used = repository.branch_counts(db).get(entry.id, 0)
    if used:
        raise DomainError(messages.catalog_in_use(entry.name, used), status=CONFLICT)
    db.delete(entry)
    db.commit()


def update(db: Session, admin: User, ingredient_id: str, values: dict) -> Ingredient:
    row = get(db, None, ingredient_id)
    _guard_branch(admin, row)
    name = catalog.tidy(values["name"] or "") if "name" in values else None
    if "name" in values and not name:
        raise DomainError(messages.NAME_REQUIRED)
    unit_id = values.get("unit_id")
    if unit_id is not None:
        _check_unit(db, unit_id)
    renamed = name is not None and name != row.name
    reunited = unit_id is not None and unit_id != row.unit_id
    entry = repository.catalog_entry(db, row.catalog_id) if row.catalog_id else None
    if entry is not None and (renamed or reunited):
        if admin.locked_outlet_id and catalog.linked_outside(db, entry, admin.locked_outlet_id):
            raise DomainError(messages.SHARED_ELSEWHERE, status=FORBIDDEN)
        catalog.rename(db, entry, name if renamed else None, unit_id if reunited else None)
    else:
        if renamed:
            if repository.named_in_branch(db, row.outlet_id, name, except_id=row.id):
                raise DomainError(messages.already_in_branch(name), status=CONFLICT)
            row.name = name
        if reunited:
            row.unit_id = unit_id
    if "category_id" in values:
        _check_category(db, values["category_id"])
        row.category_id = values["category_id"] or None
    if values.get("is_indirect") and not row.is_indirect:
        in_recipes = repository.impact(db, row.id)[0]
        if in_recipes:
            raise DomainError(messages.INDIRECT_STILL_IN_RECIPES.format(count=in_recipes), code="INDIRECT_INGREDIENT_IN_RECIPE")
    for field in UPDATABLE:
        if values.get(field) is not None:
            setattr(row, field, values[field])
    db.commit()
    return row


def impact(db: Session, admin: User, ingredient_id: str) -> tuple[int, int]:
    row = get(db, admin.locked_outlet_id, ingredient_id)
    return repository.impact(db, row.id)


def delete(db: Session, admin: User, ingredient_id: str) -> None:
    """Removing means removing: its recipe lines and movements go with it, and the screen says so beforehand."""
    row = get(db, admin.locked_outlet_id, ingredient_id)
    photo, catalog_id = row.photo_path, row.catalog_id
    repository.delete_dependents(db, row.id)
    db.delete(row)
    db.flush()
    catalog.clean_if_unused(db, catalog_id)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise DomainError(messages.STILL_USED, status=CONFLICT) from error
    uploads.discard(db, photo)


def set_photo(db: Session, admin: User, ingredient_id: str, image: UploadedFile, rule: UploadRule) -> Ingredient:
    row = get(db, admin.locked_outlet_id, ingredient_id)
    path = f"{PHOTO_FOLDER}/{row.id}/{uuid.uuid4()}{image.extension}"
    uploads.store(db, path, image, rule)
    previous = row.photo_path
    row.photo_path = path
    db.commit()
    uploads.discard(db, previous)
    return row


def remove_photo(db: Session, admin: User, ingredient_id: str) -> Ingredient:
    row = get(db, admin.locked_outlet_id, ingredient_id)
    previous = row.photo_path
    row.photo_path = None
    db.commit()
    uploads.discard(db, previous)
    return row


def _starting_unit_price(package_price: Decimal, package_size: Decimal) -> Decimal:
    """Only the first value; afterwards the price per unit is changed by hand."""
    return (package_price / package_size).quantize(UNIT_PRICE_PLACES) if package_size > 0 else Decimal(0)


def _guard_branch(admin: User, row: Ingredient) -> None:
    if admin.locked_outlet_id and row.outlet_id != admin.locked_outlet_id:
        raise DomainError(messages.NOT_FOUND, status=NOT_FOUND)


def _check_unit(db: Session, unit_id: str) -> None:
    if not repository.unit_exists(db, unit_id):
        raise DomainError(messages.UNIT_UNKNOWN)


def _check_category(db: Session, category_id: str | None) -> None:
    if category_id and not repository.category_exists(db, category_id):
        raise DomainError(messages.CATEGORY_UNKNOWN)


def describe(db: Session, rows: list[Ingredient], base_url: str) -> list[IngredientOut]:
    """Balances, last movements and names are read once for the whole page, not per row."""
    ids = [row.id for row in rows]
    balances = repository.balances(db, ids) if ids else {}
    moves = repository.last_moves(db, ids) if ids else {}
    counts = repository.branch_counts(db)
    categories = repository.names_of(db, {row.category_id for row in rows}, Category)
    units = repository.names_of(db, {row.unit_id for row in rows}, Unit)
    return [
        ingredient_out(
            row,
            base_url,
            balance=balances.get(row.id, Decimal(0)),
            last_move=moves.get(row.id),
            branch_count=counts.get(row.catalog_id, 1) if row.catalog_id else 1,
            category=categories.get(row.category_id),
            unit=units.get(row.unit_id),
        )
        for row in rows
    ]
