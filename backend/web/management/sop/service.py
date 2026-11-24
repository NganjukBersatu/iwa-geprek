"""Writing procedures: global or for one branch, slides replaced whole, the version up on every save, drafts kept per person."""
import json
import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.clock import now
from app.core.errors import DomainError
from app.core.user_names import user_names
from app.employee.sop import messages as reader_messages
from app.models.sop import Sop, SopDraft, SopSlide
from app.models.user import User
from web.management.sop import media, messages, repository
from web.management.sop.constants import FIRST_VERSION, FORBIDDEN, NOT_FOUND
from web.management.sop.domain import SopContent
from web.management.sop.schemas import DraftContentIn


@dataclass(frozen=True)
class Names:
    """Who and where, resolved once for a whole list."""

    outlets: dict[str, str]
    user: dict[str, str]
    drafted: set[str]
    # Orang yang membuka SOP per cabang dan pembaca versi terbaru per SOP, untuk kolom Dibaca.
    audience: dict[str | None, int]
    current_reads: dict[str, int]

    def audience_of(self, sop: Sop) -> int:
        if sop.outlet_id is None:
            return sum(self.audience.values())
        return self.audience.get(sop.outlet_id, 0) + self.audience.get(None, 0)


def list_visible(db: Session, user: User) -> list[Sop]:
    return repository.visible(db, user.locked_outlet_id)


def names_for(db: Session, user: User, sops: list[Sop]) -> Names:
    return Names(
        outlets=repository.outlet_names(db, {sop.outlet_id for sop in sops if sop.outlet_id}),
        user=user_names(db, {person for sop in sops for person in (sop.created_by_id, sop.updated_by_id) if person}),
        drafted={draft.sop_id for draft in repository.drafts_of(db, user.id) if draft.sop_id},
        audience=repository.audience_by_outlet(db, user.locked_outlet_id),
        current_reads=repository.current_read_counts(db, user.locked_outlet_id),
    )


@dataclass(frozen=True)
class ReaderPage:
    rows: list[repository.ReaderRow]
    total: int
    page: int
    size: int
    current: int
    audience: int
    version: int
    title: str


def readers(
    db: Session, user: User, sop_id: str, outlet_id: str | None, read: bool | None, sort: str | None, page: int, size: int
) -> ReaderPage:
    sop = get(db, user, sop_id)
    rows, total, current, audience = repository.readers_page(db, sop, user.locked_outlet_id, outlet_id, read, sort, page, size)
    return ReaderPage(rows=rows, total=total, page=page, size=size, current=current, audience=audience, version=sop.version, title=sop.title)


def get(db: Session, user: User, sop_id: str) -> Sop:
    sop = repository.find(db, sop_id)
    locked = user.locked_outlet_id
    # A branch-bound account cannot tell another branch's procedure from a missing one.
    if sop is None or (locked and sop.outlet_id not in (None, locked)):
        raise DomainError(reader_messages.NOT_FOUND, status=NOT_FOUND)
    return sop


def create(db: Session, user: User, content: SopContent, draft_id: str | None) -> Sop:
    current = now()
    sop = Sop(
        id=str(uuid.uuid4()),
        version=FIRST_VERSION,
        sort_order=repository.next_sort_order(db),
        created_at=current,
        updated_at=current,
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    _apply(sop, content, _writable_outlet(user, content.outlet_id))
    db.add(sop)
    _drop_own_draft(db, user, draft_id)
    db.commit()
    db.refresh(sop)
    return sop


def update(db: Session, user: User, sop_id: str, content: SopContent) -> Sop:
    sop = _writable(db, user, sop_id)
    before = media.names_in(slide.body for slide in sop.slides)
    _apply(sop, content, _writable_outlet(user, content.outlet_id))
    sop.version += 1
    sop.updated_at = now()
    sop.updated_by_id = user.id
    existing = repository.draft_for(db, user.id, sop.id)
    if existing is not None:
        db.delete(existing)
    db.commit()
    db.refresh(sop)
    media.discard_unused(db, before, media.names_in(slide.body for slide in sop.slides))
    return sop


def delete(db: Session, user: User, sop_id: str) -> None:
    sop = _writable(db, user, sop_id)
    before = media.names_in(slide.body for slide in sop.slides)
    db.delete(sop)
    db.commit()
    media.discard_unused(db, before, set())


def reorder(db: Session, user: User, ids: list[str]) -> list[Sop]:
    """The list arrives whole, top first; a list that no longer matches the server's is refused rather than half applied."""
    if user.locked_outlet_id:
        raise DomainError(messages.ORDER_LOCKED, status=FORBIDDEN)
    sops = list_visible(db, user)
    if sorted(ids) != sorted(sop.id for sop in sops):
        raise DomainError(messages.ORDER_MISMATCH)
    by_id = {sop.id: sop for sop in sops}
    for position, sop_id in enumerate(ids):
        by_id[sop_id].sort_order = position
    db.commit()
    return list_visible(db, user)


def drafts(db: Session, user: User) -> list[SopDraft]:
    return repository.drafts_of(db, user.id)


def read_draft(db: Session, user: User, draft_id: str) -> SopDraft:
    draft = repository.find_draft(db, draft_id)
    if draft is None or draft.user_id != user.id:
        raise DomainError(messages.DRAFT_NOT_FOUND, status=NOT_FOUND)
    return draft


def save_draft(db: Session, user: User, draft_id: str | None, sop_id: str | None, base_version: int | None, content: DraftContentIn) -> SopDraft:
    """Called after every pause in typing; one draft per person per procedure, so saving again overwrites it."""
    if sop_id is not None:
        get(db, user, sop_id)
        draft = repository.draft_for(db, user.id, sop_id)
    else:
        draft = repository.find_draft(db, draft_id) if draft_id else None
        if draft is not None and draft.user_id != user.id:
            raise DomainError(messages.DRAFT_NOT_FOUND, status=NOT_FOUND)
    if draft is None:
        draft = SopDraft(id=str(uuid.uuid4()), user_id=user.id, sop_id=sop_id, base_version=base_version)
        db.add(draft)
    draft.content = content.model_dump_json()
    draft.updated_at = now()
    db.commit()
    db.refresh(draft)
    return draft


def discard_draft(db: Session, user: User, draft_id: str) -> None:
    draft = read_draft(db, user, draft_id)
    db.delete(draft)
    db.commit()


def draft_content(draft: SopDraft) -> DraftContentIn:
    return DraftContentIn.model_validate(json.loads(draft.content))


def _writable(db: Session, user: User, sop_id: str) -> Sop:
    sop = get(db, user, sop_id)
    if user.locked_outlet_id and sop.outlet_id is None:
        raise DomainError(messages.GLOBAL_LOCKED, status=FORBIDDEN)
    return sop


def _writable_outlet(user: User, wanted: str | None) -> str | None:
    """A branch-bound account always writes for its own branch; only an unbound one may write for every branch."""
    locked = user.locked_outlet_id
    if locked is None:
        return wanted
    if wanted not in (None, locked):
        raise DomainError(messages.OTHER_BRANCH, status=FORBIDDEN)
    return locked


def _drop_own_draft(db: Session, user: User, draft_id: str | None) -> None:
    draft = repository.find_draft(db, draft_id) if draft_id else None
    if draft is not None and draft.user_id == user.id:
        db.delete(draft)


def _apply(sop: Sop, content: SopContent, outlet_id: str | None) -> None:
    sop.title = content.title.strip()
    sop.active = content.active
    sop.outlet_id = outlet_id
    sop.slides = [
        SopSlide(id=str(uuid.uuid4()), sort_order=position, title=slide.title.strip(), body=slide.body)
        for position, slide in enumerate(content.slides)
    ]
