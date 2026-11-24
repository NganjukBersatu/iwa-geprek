"""Linking an employee to a tablet: the tablet shows a QR, the employee scans it, the tablet hears it at once."""
import secrets
import uuid
from collections.abc import AsyncIterator
from datetime import timedelta

from sqlalchemy.orm import Session

from app.core import live
from app.core.auth import CHANNEL_BEARER, start_session
from app.core.clock import as_aware, now
from app.core.database import SessionLocal
from app.core.errors import DomainError
from app.core.security import hash_token
from app.employee.devices import messages, repository
from app.employee.devices.constants import (
    NOT_FOUND,
    QR_DEVICE_LABEL,
    QR_EXPIRED,
    QR_LIFETIME_SECONDS,
    QR_LINKED,
    QR_TABLES,
    QR_TOKEN_BYTES,
    QR_WAITING,
    USER_TOKEN_WINDOW_SECONDS,
)
from app.employee.devices.schemas import QrStatusOut
from app.models.device import REGISTERED, Device, DeviceLink
from app.models.user import User


def link(db: Session, user: User, token: str) -> Device:
    """Every failure about the QR itself gets the same sentence, so a code cannot be guessed from the answers."""
    instant = now()
    link_row = repository.find_link_for_update(db, hash_token(token))
    if link_row is None or link_row.user_id is not None or as_aware(link_row.expires_at) < instant:
        raise DomainError(messages.INVALID_QR)
    device = repository.find_device(db, link_row.device_id)
    if device is None or device.status != REGISTERED:
        raise DomainError(messages.INVALID_QR)
    # The caller is signed in and holds a real QR, so the branch mismatch gets its own sentence.
    if user.working_outlet_id and user.working_outlet_id != device.outlet_id:
        raise DomainError(messages.OTHER_BRANCH)
    link_row.user_id = user.id
    link_row.linked_at = instant
    db.commit()
    return device


def issue_qr(db: Session, device: Device) -> tuple[DeviceLink, str]:
    """A new QR replaces any unused one; only its hash is kept."""
    repository.drop_unused_links(db, device.id)
    token = secrets.token_urlsafe(QR_TOKEN_BYTES)
    link_row = DeviceLink(
        id=str(uuid.uuid4()),
        device_id=device.id,
        token_hash=hash_token(token),
        expires_at=now() + timedelta(seconds=QR_LIFETIME_SECONDS),
    )
    db.add(link_row)
    db.commit()
    return link_row, token


def ensure_own_qr(db: Session, device_id: str, link_id: str) -> None:
    link_row = repository.find_link(db, link_id)
    if link_row is None or link_row.device_id != device_id:
        raise DomainError(messages.QR_NOT_FOUND, status=NOT_FOUND)


def _snapshot(device_id: str, link_id: str) -> live.Snapshot:
    with SessionLocal() as db:
        link_row = repository.find_link(db, link_id)
        instant = now()
        if link_row is None or link_row.device_id != device_id:
            return live.Snapshot("status", QrStatusOut(status=QR_EXPIRED).model_dump(), final=True, seconds_left=0)
        if link_row.user_id is not None:
            user = db.get(User, link_row.user_id)
            fresh = link_row.linked_at is not None and instant - as_aware(link_row.linked_at) <= timedelta(seconds=USER_TOKEN_WINDOW_SECONDS)
            token = start_session(db, user, CHANNEL_BEARER, QR_DEVICE_LABEL)[0] if user and user.is_active and fresh else None
            name = (user.name or user.username) if user else None
            return live.Snapshot("status", QrStatusOut(status=QR_LINKED, user_name=name, access_token=token).model_dump(), final=True, seconds_left=0)
        left = (as_aware(link_row.expires_at) - instant).total_seconds()
        if left <= 0:
            return live.Snapshot("status", QrStatusOut(status=QR_EXPIRED).model_dump(), final=True, seconds_left=0)
        return live.Snapshot("status", QrStatusOut(status=QR_WAITING).model_dump(), final=False, seconds_left=left)


def watch_qr(device_id: str, link_id: str) -> AsyncIterator[str]:
    return live.record(QR_TABLES, lambda: _snapshot(device_id, link_id))
