"""Database reads for device links."""
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.device import Device, DeviceLink


def find_link_for_update(db: Session, token_hash: str) -> DeviceLink | None:
    """The row stays locked until the transaction ends, so two scans of one QR cannot both succeed."""
    return db.scalar(select(DeviceLink).where(DeviceLink.token_hash == token_hash).with_for_update())


def find_device(db: Session, device_id: str) -> Device | None:
    return db.get(Device, device_id)


def drop_unused_links(db: Session, device_id: str) -> None:
    db.execute(delete(DeviceLink).where(DeviceLink.device_id == device_id, DeviceLink.user_id.is_(None)))


def find_link(db: Session, link_id: str) -> DeviceLink | None:
    return db.get(DeviceLink, link_id)
