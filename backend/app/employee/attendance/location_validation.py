"""Checks the reported position against the branch radius and the rules for working outside it."""
import math
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.core.geo import distance_meters
from app.employee.attendance import messages
from app.employee.attendance.constants import LOCATION_OUTSIDE
from app.models.outlet import Outlet


@dataclass(frozen=True)
class Location:
    latitude: float
    longitude: float
    accuracy: float
    mode: str
    note: str | None


@dataclass(frozen=True)
class Distance:
    meters: float | None
    radius: int | None


def validate_location(db: Session, outlet_id: str, location: Location) -> Distance:
    if not all(math.isfinite(value) for value in (location.latitude, location.longitude, location.accuracy)):
        raise DomainError(messages.INVALID_LOCATION)
    if location.mode == LOCATION_OUTSIDE and not (location.note or "").strip():
        raise DomainError(messages.OUTSIDE_NOTE_REQUIRED)

    branch = db.get(Outlet, outlet_id)
    if branch is None:
        return Distance(meters=None, radius=None)

    meters = None
    if branch.latitude is not None and branch.longitude is not None:
        meters = distance_meters(location.latitude, location.longitude, branch.latitude, branch.longitude)
    radius = branch.attendance_radius_meters
    beyond_radius = meters is not None and radius is not None and meters > radius
    if location.mode != LOCATION_OUTSIDE and beyond_radius:
        raise DomainError(messages.OUTSIDE_RADIUS.format(distance=round(meters), radius=radius))
    return Distance(meters=meters, radius=radius)
