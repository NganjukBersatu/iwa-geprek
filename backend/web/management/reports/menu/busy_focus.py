"""Diving into one hour of the busiest-times reports, where the hour slots turn into minutes."""
from app.core.errors import DomainError
from web.management.reports.menu import messages
from web.management.reports.menu.constants import UNIT_HOUR, UNIT_MINUTE


def effective_unit(unit: str, hour: int | None) -> str:
    """Diving into one hour shows its minutes; asking that of any other unit is refused rather than ignored."""
    if hour is None:
        return unit
    if unit != UNIT_HOUR:
        raise DomainError(messages.MINUTES_NEED_HOUR_UNIT)
    return UNIT_MINUTE
