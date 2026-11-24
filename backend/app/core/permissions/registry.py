"""All groups in the order the role screen lists them, and what the rest of the code needs to know about them."""
from app.core.permissions import branch, cashier, catalog, customers, expenses, figures, people, stock
from app.core.permissions.model import Group

GROUPS: tuple[Group, ...] = (
    cashier.GROUP,
    stock.GROUP,
    customers.GROUP,
    catalog.GROUP,
    expenses.GROUP,
    people.GROUP,
    branch.GROUP,
    figures.GROUP,
)

ALL_KEYS: frozenset[str] = frozenset(
    permission.key for group in GROUPS for section in group.sections for permission in section.permissions
)

# Ticked already when a new role is added; the owner can still untick them.
DEFAULT_FOR_NEW_ROLE: frozenset[str] = frozenset(
    permission.key
    for group in GROUPS
    for section in group.sections
    for permission in section.permissions
    if permission.default_for_new_role
)
