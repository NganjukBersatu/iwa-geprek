"""Turns the voids report into its response schema."""
from web.management.reports.menu.voids.domain import Voids
from web.management.reports.menu.voids.schemas import VoidedOrderOut, VoidsByUserOut, VoidsOut


def voids_out(report: Voids) -> VoidsOut:
    fields = {name: value for name, value in vars(report).items() if name not in ("by_user", "orders")}
    return VoidsOut(
        **fields,
        by_user=[VoidsByUserOut(**vars(tally)) for tally in report.by_user],
        orders=[VoidedOrderOut(**vars(order)) for order in report.orders],
    )
