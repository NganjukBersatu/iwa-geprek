"""Runs the detectors the person may see and puts their findings in one order."""
from sqlalchemy.orm import Session

from app.core.auth import passes
from app.core.branches import outlets_in_scope
from app.core.clock import now, today
from app.models.user import User
from web.management.issues.domain import LEVEL_ORDER, Issue, IssueKind, Scope
from web.management.issues.registry import DETECTORS, PERMISSION_OF

KIND_ORDER = {kind: position for position, kind in enumerate(IssueKind)}


def issues(db: Session, user: User, outlet_id: str | None) -> tuple[list[Issue], dict[str, str]]:
    """The findings, most serious first, and the names of the branches they name."""
    allowed = {kind for kind, permission in PERMISSION_OF.items() if passes(user, permission)}
    outlets = outlets_in_scope(db, outlet_id)
    scope = Scope(db=db, outlet_id=outlet_id, outlet_ids=[outlet.id for outlet in outlets], today=today(), now=now())
    found = [issue for detector in DETECTORS if allowed.intersection(detector.kinds) for issue in detector.run(scope) if issue.kind in allowed]
    names = {outlet.id: outlet.name for outlet in outlets}
    found.sort(key=lambda issue: (LEVEL_ORDER[issue.level], KIND_ORDER[issue.kind], names.get(issue.outlet_id or "", ""), issue.subject.lower()))
    return found, names
