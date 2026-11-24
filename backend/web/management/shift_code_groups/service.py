"""Shift codes as the admin thinks of them: one code, used by one or many branches.

Underneath stay the rows of the shift code table, one per branch, tied together by their master id.
Every change here goes through the row service, so the rules of a single code still apply to each row.
"""
import uuid

from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.models.category import Category
from app.models.shift_code import ShiftCode
from app.models.user import User
from web.management.shift_code_groups import messages, repository
from web.management.shift_code_groups.constants import CATEGORY_KIND, CONFLICT, NOT_FOUND
from web.management.shift_code_groups.domain import CodeGroup, GroupChanges, GroupDraft
from web.management.shift_codes import repository as row_repository
from web.management.shift_codes import service as row_service
from web.management.shift_codes.domain import ShiftCodeChanges, ShiftCodeDraft


def list_groups(db: Session, admin: User) -> list[CodeGroup]:
    return _group(db, repository.rows(db, admin.locked_outlet_id))


def category_names(db: Session) -> list[str]:
    return repository.category_names(db, CATEGORY_KIND)


def create_group(db: Session, admin: User, draft: GroupDraft) -> CodeGroup:
    outlet_ids = _allowed_outlets(db, admin, draft.outlet_ids)
    code = draft.code.strip()
    if row_repository.any_named(db, code):
        raise DomainError(messages.CODE_EXISTS.format(code=code), status=CONFLICT, field="code")
    category_id = _category_id(db, draft.category)
    created: list[ShiftCode] = []
    try:
        for outlet_id in outlet_ids:
            created.append(row_service.create(db, outlet_id, _row_draft(draft, category_id, code)))
    except DomainError:
        for row in created:
            db.delete(row)
        db.commit()
        raise
    return _one(db, admin, created[0].master_id or created[0].id)


def update_group(db: Session, admin: User, key: str, changes: GroupChanges) -> CodeGroup:
    rows = _rows(db, admin, key)
    values = dict(changes.values)
    if changes.category is not None:
        values["category_id"] = _category_id(db, changes.category)
    new_code = values.get("code")
    if new_code is not None:
        new_code = values["code"] = new_code.strip()
        _ensure_rename_free(db, rows, new_code)

    for row in rows:
        row_service.update(db, admin, row.id, ShiftCodeChanges(values=dict(values), crosses_midnight=changes.crosses_midnight))

    if changes.outlet_ids is not None and not admin.locked_outlet_id:
        _set_branches(db, admin, key, rows, changes.outlet_ids)
    return _one(db, admin, key)


def get_group(db: Session, admin: User, key: str) -> CodeGroup:
    """One group for its page; a group none of whose codes this admin may see answers as missing."""
    _rows(db, admin, key)
    return _one(db, admin, key)


def delete_group(db: Session, admin: User, key: str) -> None:
    """Schedules using the code stay and only lose it, as with a single code."""
    for row in _rows(db, admin, key):
        row_service.delete(db, admin, row.id)


def _set_branches(db: Session, admin: User, key: str, rows: list[ShiftCode], wanted: tuple[str, ...]) -> None:
    outlet_ids = set(_allowed_outlets(db, admin, wanted))
    present = {row.outlet_id for row in rows}
    template = repository.rows_of_group(db, key, None)[0]
    for outlet_id in outlet_ids - present:
        row_service.create(
            db,
            outlet_id,
            ShiftCodeDraft(
                category_id=template.category_id or "",
                code=template.code,
                start_clock=template.start_clock,
                end_clock=template.end_clock,
                overtime_start_clock=template.overtime_start_clock,
                overtime_end_clock=template.overtime_end_clock,
                color=template.color,
                is_day_off=template.is_day_off,
                sort_order=template.sort_order,
            ),
        )
    for row in rows:
        if row.outlet_id not in outlet_ids:
            row_service.delete(db, admin, row.id)


def _row_draft(draft: GroupDraft, category_id: str, code: str) -> ShiftCodeDraft:
    return ShiftCodeDraft(
        category_id=category_id,
        code=code,
        start_clock=draft.start_clock,
        end_clock=draft.end_clock,
        overtime_start_clock=draft.overtime_start_clock,
        overtime_end_clock=draft.overtime_end_clock,
        color=draft.color,
        is_day_off=draft.is_day_off,
        sort_order=draft.sort_order,
        crosses_midnight=draft.crosses_midnight,
    )


def _ensure_rename_free(db: Session, rows: list[ShiftCode], code: str) -> None:
    """Renaming must not collide with another code of any branch the group sits in."""
    own = {row.id for row in rows}
    for outlet in repository.outlets(db):
        owner = row_repository.code_owner(db, outlet.id, code)
        if owner is not None and owner.id not in own:
            raise DomainError(messages.CODE_TAKEN.format(code=code, branch=outlet.name), status=CONFLICT, field="code")


def _allowed_outlets(db: Session, admin: User, outlet_ids: tuple[str, ...]) -> list[str]:
    locked = admin.locked_outlet_id
    if locked:
        return [locked]
    if not outlet_ids:
        raise DomainError(messages.BRANCH_REQUIRED, field="outlet_ids")
    known = {outlet.id for outlet in repository.outlets(db)}
    if any(outlet_id not in known for outlet_id in outlet_ids):
        raise DomainError(messages.BRANCH_UNKNOWN, field="outlet_ids")
    return list(dict.fromkeys(outlet_ids))


def _category_id(db: Session, name: str) -> str:
    """A category is found by its name, or made when it is new, so no separate screen is needed for it."""
    tidy = " ".join(name.split())
    if not tidy:
        raise DomainError(messages.CATEGORY_REQUIRED, field="category")
    found = repository.category_named(db, CATEGORY_KIND, tidy)
    if found is not None:
        return found.id
    category = Category(id=str(uuid.uuid4()), kind=CATEGORY_KIND, name=tidy)
    db.add(category)
    db.flush()
    return category.id


def _rows(db: Session, admin: User, key: str) -> list[ShiftCode]:
    rows = repository.rows_of_group(db, key, admin.locked_outlet_id)
    if not rows:
        raise DomainError(messages.NOT_FOUND, status=NOT_FOUND)
    return rows


def _one(db: Session, admin: User, key: str) -> CodeGroup:
    return next(group for group in list_groups(db, admin) if group.key == key)


def _group(db: Session, rows: list[ShiftCode]) -> list[CodeGroup]:
    outlets = {outlet.id: outlet for outlet in repository.outlets(db)}
    used = repository.assignments_by_code(db)
    grouped: dict[str, list[ShiftCode]] = {}
    for row in rows:
        grouped.setdefault(row.master_id or row.id, []).append(row)
    groups = []
    for key, members in grouped.items():
        branches = sorted((outlets[row.outlet_id] for row in members if row.outlet_id in outlets), key=lambda outlet: outlet.name)
        first = members[0]
        groups.append(
            CodeGroup(
                key=key,
                rows=members,
                branches=branches,
                assignments=sum(used.get(row.id, 0) for row in members),
                category=first.category.name if first.category else "",
            )
        )
    return groups
