"""Turns cash sessions into the choices of the expense form."""
from app.models.cash_session import CashSession, CashSessionStatus
from web.management.expenses.schemas import SessionChoiceOut


def session_choice_out(session: CashSession, username: str) -> SessionChoiceOut:
    return SessionChoiceOut(
        id=session.id,
        outlet_id=session.outlet_id,
        business_day=session.business_day,
        cashier_username=username,
        shift_code=session.shift_code,
        opened_at=session.opened_at,
        running=session.status == CashSessionStatus.OPEN,
        has_shopping_fund=session.planned_shopping is not None,
    )
