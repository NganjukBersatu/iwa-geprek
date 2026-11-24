from app.core.http import static_url
from app.core.sorting import RowSorting
from app.models.deposit import Deposit
from web.management.deposits.schemas import STATUS_ORDER, DepositDayShareOut, DepositDayStateOut, DepositOut

DAY_SORTING: RowSorting[DepositDayStateOut] = RowSorting(
    keys={
        "day": lambda row: row.day,
        "due": lambda row: row.due,
        "status": lambda row: STATUS_ORDER.index(row.status),
        "paid": lambda row: row.paid,
        "left": lambda row: row.left,
    },
    identity=lambda row: row.day.isoformat(),
)

SHARE_SORTING: RowSorting[DepositDayShareOut] = RowSorting(
    keys={"day": lambda row: row.day, "amount": lambda row: row.amount},
    identity=lambda row: row.day.isoformat(),
)


def deposit_out(deposit: Deposit, user_name: str | None, base_url: str, outlet_name: str, share_sort: str | None = None) -> DepositOut:
    return DepositOut(
        id=deposit.id,
        outlet_id=deposit.outlet_id,
        outlet_name=outlet_name,
        deposit_date=deposit.deposit_date,
        amount=deposit.amount,
        note=deposit.note,
        photo_url=static_url(base_url, deposit.photo_path),
        user_name=user_name,
        days=SHARE_SORTING.apply([DepositDayShareOut(day=share.day, amount=share.amount) for share in deposit.days], share_sort),
        created_at=deposit.created_at,
    )
