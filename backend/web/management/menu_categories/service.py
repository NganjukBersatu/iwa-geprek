"""Managing the categories of the menu; a category decides which station makes a menu and which printer its ticket goes to."""
import unicodedata
import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.models.category import Category
from web.management.menu_categories import messages, repository
from web.management.menu_categories.constants import CATEGORY_KIND, CONFLICT, MAX_CATEGORIES, NOT_FOUND
from web.management.menu_categories.repository import Row


def _clean(name: str) -> str:
    tidy = " ".join(unicodedata.normalize("NFC", name).split())
    if not tidy:
        raise DomainError(messages.NAME_REQUIRED, field="name")
    return tidy


def _taken(name: str) -> DomainError:
    return DomainError(messages.NAME_TAKEN.format(name=name), status=CONFLICT, field="name")


def _free(db: Session, name: str, own_id: str | None) -> None:
    clash = repository.named(db, name)
    if clash is not None and clash.id != own_id:
        raise _taken(clash.name)


def _commit(db: Session, name: str) -> None:
    """The unique index is the referee when two requests use the same name at once."""
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise _taken(name) from error


def _row(db: Session, category_id: str) -> Row:
    row = repository.detail(db, category_id)
    if row is None:
        raise DomainError(messages.NOT_FOUND, status=NOT_FOUND)
    return row


def list_categories(db: Session) -> list[Row]:
    return repository.listing(db)


def create(db: Session, name: str) -> Row:
    tidy = _clean(name)
    if repository.total(db) >= MAX_CATEGORIES:
        raise DomainError(messages.LIMIT_REACHED.format(limit=MAX_CATEGORIES), status=CONFLICT)
    _free(db, tidy, None)
    category = Category(id=str(uuid.uuid4()), kind=CATEGORY_KIND, name=tidy)
    db.add(category)
    _commit(db, tidy)
    return _row(db, category.id)


def update(db: Session, category_id: str, name: str) -> Row:
    category = repository.find(db, category_id, lock=True)
    if category is None:
        raise DomainError(messages.NOT_FOUND, status=NOT_FOUND)
    tidy = _clean(name)
    if tidy != category.name:
        _free(db, tidy, category.id)
        category.name = tidy
        _commit(db, tidy)
    return _row(db, category_id)


def delete(db: Session, category_id: str) -> None:
    """A category still holding menus is refused, since the menus would lose the station that makes them; its station mapping goes with it."""
    category = repository.find(db, category_id, lock=True)
    if category is None:
        raise DomainError(messages.NOT_FOUND, status=NOT_FOUND)
    count = repository.menu_count(db, category_id)
    if count > 0:
        db.rollback()
        raise DomainError(messages.STILL_USED.format(name=category.name, count=count), status=CONFLICT)
    db.delete(category)
    db.commit()
