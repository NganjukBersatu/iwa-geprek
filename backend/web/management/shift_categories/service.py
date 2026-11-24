"""The settings admins give shift categories: the kind (work or day off) and the range a shift may start in."""
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.models.category import Category
from app.models.shift_code import ShiftCode
from app.models.user import User
from web.management.shift_categories import messages, repository
from web.management.shift_categories.constants import CATEGORY_KIND, CONFLICT, FORBIDDEN, KIND_OFF, NOT_FOUND
from web.management.shift_categories.domain import CategoryChanges, CategoryEntry
from web.management.shift_codes import category_rules


def list_categories(db: Session) -> list[CategoryEntry]:
    categories = repository.categories(db, CATEGORY_KIND)
    codes = repository.codes_by_category(db)
    return [_entry(category, codes.get(category.id, [])) for category in categories]


def update(db: Session, admin: User, category_id: str, changes: CategoryChanges) -> CategoryEntry:
    # Satu kategori dipakai semua cabang, jadi admin yang terikat satu cabang tidak boleh mengubahnya.
    if admin.locked_outlet_id:
        raise DomainError(messages.ALL_BRANCHES_ONLY, status=FORBIDDEN, code="SHIFT_CATEGORY_ALL_BRANCHES_ONLY")
    category = repository.find(db, CATEGORY_KIND, category_id)
    if category is None:
        raise DomainError(messages.NOT_FOUND, status=NOT_FOUND)
    if "name" in changes.given:
        category.name = _free_name(db, category, changes.name)
    if "shift_kind" in changes.given:
        category.shift_kind = changes.shift_kind
    if "start_from" in changes.given:
        category.shift_start_from = changes.start_from
    if "start_until" in changes.given:
        category.shift_start_until = changes.start_until
    _check(category)
    db.commit()
    db.refresh(category)
    return _entry(category, repository.codes_by_category(db, [category.id]).get(category.id, []))


def delete(db: Session, category_id: str) -> None:
    """Hanya kategori yang tidak dipakai kode mana pun; yang masih dipakai tetap ada supaya kodenya tidak kehilangan kategori."""
    category = repository.find_for_update(db, CATEGORY_KIND, category_id)
    if category is None:
        raise DomainError(messages.NOT_FOUND, status=NOT_FOUND)
    in_use = repository.code_count(db, category.id)
    if in_use > 0:
        name = category.name
        db.rollback()
        raise DomainError(messages.IN_USE.format(name=name, count=in_use), status=CONFLICT, code="SHIFT_CATEGORY_IN_USE")
    db.delete(category)
    db.commit()


def _free_name(db: Session, category: Category, name: str | None) -> str:
    tidy = " ".join((name or "").split())
    if not tidy:
        raise DomainError(messages.NAME_REQUIRED, field="name")
    owner = repository.name_owner(db, CATEGORY_KIND, tidy)
    if owner is not None and owner.id != category.id:
        raise DomainError(messages.NAME_TAKEN.format(name=tidy), status=CONFLICT, field="name")
    return tidy


def _check(category: Category) -> None:
    """Pemeriksaan yang sama dengan CHECK di database, supaya admin mendapat kalimat yang jelas, bukan galat database."""
    start, end = category.shift_start_from, category.shift_start_until
    if bool(start) != bool(end):
        raise DomainError(messages.WINDOW_UNPAIRED, field="start_until")
    if start and end and start == end:
        raise DomainError(messages.WINDOW_SAME_CLOCK, field="start_until")
    if category.shift_kind == KIND_OFF and (start or end):
        raise DomainError(messages.OFF_HAS_NO_WINDOW, field="shift_kind")


def _entry(category: Category, codes: list[ShiftCode]) -> CategoryEntry:
    mismatched = sum(
        1 for code in codes if category_rules.violation(category, is_day_off=code.is_day_off, start_clock=code.start_clock) is not None
    )
    return CategoryEntry(category=category, codes=len(codes), mismatched=mismatched)
