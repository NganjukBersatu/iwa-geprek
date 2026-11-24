import { termText } from '$lib/text/terms';
import { financeText } from '$lib/text/finance';
/** The words for each fund source the server sends, shared by every finance screen. */
export const FUND_SOURCES: Record<string, string> = {
	kas_laci: financeText.cashRevenue,
	uang_belanja: termText.spendingFloat,
	dana_lain: financeText.otherFunds
};
