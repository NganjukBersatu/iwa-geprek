from datetime import date
from decimal import Decimal

from app.core.errors import DomainError
from web.management.deposits import messages
from web.management.deposits.constants import OPEN, PARTIAL, SETTLED


def rupiah(value: Decimal) -> str:
    return "Rp " + f"{int(value):,}".replace(",", ".")


def status_of(due: Decimal, paid: Decimal) -> str:
    if paid <= 0:
        return OPEN
    return SETTLED if paid >= due else PARTIAL


def allocate(amount: Decimal, open_days: list[tuple[date, Decimal]]) -> dict[date, Decimal]:
    """The oldest day is settled first, so a day only gets money once every older one is full; more than the days still hold is refused."""
    room = sum((left for _, left in open_days), Decimal(0))
    if amount > room:
        raise DomainError(messages.AMOUNT_TOO_BIG.format(room=rupiah(room)))
    remaining, shares = amount, {}
    for day, left in sorted(open_days):
        if remaining <= 0:
            break
        take = min(remaining, left)
        shares[day] = take
        remaining -= take
    return shares
