import { numberInput, parseNumber } from '$lib/format/number';
import type { Expense, IngredientChoice, ReceiptReading } from '$lib/api/types';
import { formatRupiah, rupiahInput } from '$lib/format/currency';
import { FUND_SOURCES } from '../finance/fund-sources';
import { expenseText } from '$lib/text/expenses';
import { format } from '$lib/text/format';

/** One line of the receipt; with an ingredient it becomes an ingredient line, with a quantity in that ingredient's unit. */
export type ReceiptRow = {
	key: number;
	name: string;
	amount: string;
	ingredientId: string;
	quantity: string;
	/** Close ingredients the server was not sure enough to pick. */
	suggestions: IngredientChoice[];
};

let nextKey = 0;

export function emptyRow(name = '', amount = '', ingredientId = '', quantity = '', suggestions: IngredientChoice[] = []): ReceiptRow {
	return { key: nextKey++, name, amount, ingredientId, quantity, suggestions };
}

/** The saved line as a row, for editing. */
export function rowOf(expense: Expense): ReceiptRow {
	return emptyRow(expense.item_name, rupiahInput(expense.amount), expense.ingredient_id ?? '', quantityText(expense.quantity));
}

/** People type a comma, the server takes a point; empty or zero means no quantity, and a plain line never has one. */
export function quantityValue(row: ReceiptRow): string | null {
	if (!row.ingredientId) return null;
	const value = parseNumber(row.quantity);
	return value !== null && value > 0 ? String(value) : null;
}

/** "2.500" from the server shown as "2,5". */
export function quantityText(quantity: string | null | undefined): string {
	if (!quantity) return '';
	return numberInput(quantity);
}

/** The items read from the photo; with none but a printed total, one row for the whole receipt so the amount is still filled. */
export function rowsFrom(reading: ReceiptReading): ReceiptRow[] {
	if (reading.items.length > 0) {
		return reading.items.map((item) =>
			emptyRow(item.name, rupiahInput(item.amount), item.ingredient?.id ?? '', item.ingredient && item.quantity ? String(item.quantity) : '', item.ingredient ? [] : item.suggestions)
		);
	}
	if (reading.total) return [emptyRow(reading.store ? format(expenseText.purchaseAt, { store: reading.store }) : '', rupiahInput(reading.total))];
	return [emptyRow()];
}

/** What one saved receipt added, for the confirmation shown after it. */
export function recordedSummary(saved: Expense[]): string {
	const first = saved[0];
	if (!first) return expenseText.recorded;
	const total = saved.reduce((sum, expense) => sum + Number(expense.amount), 0);
	const what = saved.length === 1 ? first.item_name : format(expenseText.goodsCount, { count: saved.length });
	return format(expenseText.purchaseRecorded, { what: what, total: formatRupiah(total), source: FUND_SOURCES[first.fund_source] ?? first.fund_source });
}
