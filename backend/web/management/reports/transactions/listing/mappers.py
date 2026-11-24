"""Turns the transaction list into its response schema."""
from dataclasses import asdict

from app.core.money import decimal_of
from app.models.order import CASH_METHOD, Order
from web.management.reports.transactions import messages
from web.management.reports.transactions.listing.domain import TransactionPage
from web.management.reports.transactions.listing.schemas import MethodTotalOut, TransactionOut, TransactionsOut


def _transaction_out(order: Order, cashier_names: dict[str, str]) -> TransactionOut:
    method = order.payment_method or CASH_METHOD
    return TransactionOut(
        id=order.id,
        receipt_number=order.receipt_number,
        created_at=order.created_at,
        cashier=cashier_names.get(order.cashier_id, messages.DELETED_ACCOUNT),
        method=method,
        method_label=order.payment_method_label or method.capitalize(),
        total=decimal_of(order.total),
        voided=order.voided_at is not None,
        table_no=order.table_no,
        customer_name=order.customer_name,
    )


def transactions_out(report: TransactionPage) -> TransactionsOut:
    return TransactionsOut(
        start=report.start,
        end=report.end,
        group=report.group,
        method=report.method,
        count=report.count,
        amount=report.amount,
        by_method=[MethodTotalOut(**asdict(total)) for total in report.by_method],
        page=report.page,
        per_page=report.per_page,
        rows=[_transaction_out(order, report.cashier_names) for order in report.orders],
    )
