import type { SessionHistoryRow } from '$lib/api/types';
import { EMPTY_VALUE, formatNumber, formatRupiah, formatSigned } from '$lib/format/currency';
import { termText } from '$lib/text/terms';
import { sessionHistoryText } from '$lib/text/session-history';
import { format } from '$lib/text/format';

export type Figure = { label: string; value: string };

/** The money that went through the drawer, line by line, for any screen that shows a session. */
export function drawerFigures(row: SessionHistoryRow): Figure[] {
	return [
		{ label: sessionHistoryText.openingFloat, value: formatRupiah(row.opening_cash) },
		{ label: sessionHistoryText.cashRevenue, value: formatRupiah(row.cash_revenue) },
		{ label: sessionHistoryText.drawerExpense, value: formatRupiah(row.drawer_expenses) },
		{ label: sessionHistoryText.expectedMoney, value: formatRupiah(row.expected_cash) },
		{ label: sessionHistoryText.actualMoney, value: row.actual_cash === null ? EMPTY_VALUE : formatRupiah(row.actual_cash) },
		{ label: termText.difference, value: row.difference === null ? EMPTY_VALUE : formatSigned(row.difference) }
	];
}

/** What happened outside the drawer in the same session. */
export function outsideFigures(row: SessionHistoryRow): Figure[] {
	return [
		{ label: sessionHistoryText.nonCashRevenue, value: formatRupiah(row.non_cash_revenue) },
		{ label: sessionHistoryText.otherFundsExpense, value: formatRupiah(row.other_fund_expenses) },
		{ label: sessionHistoryText.spendingUsage, value: formatRupiah(row.shopping_fund_used) },
		{ label: termText.transaction, value: format(sessionHistoryText.validAndVoided, { valid: formatNumber(row.transactions, 0), voided: formatNumber(row.voided_transactions, 0) }) }
	];
}
