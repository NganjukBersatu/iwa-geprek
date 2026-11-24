import type { Expense } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { EMPTY_VALUE, formatRupiah } from '$lib/format/currency';
import { formatDateTime } from '$lib/format/datetime';
import { formatDate } from '$lib/date/range';
import { FUND_SOURCES } from '../finance/fund-sources';
import { quantityText } from './receipt';
import { termText } from '$lib/text/terms';
import { expenseText } from '$lib/text/expenses';

/** "Gula Pasir · 2 kg"; a plain line has none. */
function ingredientOf(row: Expense): string {
	if (!row.ingredient_name) return EMPTY_VALUE;
	const amount = [quantityText(row.quantity), row.quantity ? row.unit_name : null].filter(Boolean).join(' ');
	return amount ? `${row.ingredient_name} · ${amount}` : row.ingredient_name;
}

export const expenseColumns: Column<Expense>[] = [
	{ key: 'barang', label: termText.item, align: 'left', value: (row) => row.item_name, sort: 'item' },
	{ key: 'bahan', label: termText.ingredient, align: 'left', value: ingredientOf, sort: 'ingredient' },
	{ key: 'cabang', label: termText.branch, align: 'left', value: (row) => row.outlet_name ?? EMPTY_VALUE, sort: 'outlet' },
	{ key: 'hari', label: termText.day, align: 'left', value: (row) => formatDate(row.business_day), sort: 'business_day' },
	{ key: 'waktu', label: termText.recordedAt, align: 'left', value: (row) => formatDateTime(row.created_at), sort: 'created_at' },
	{ key: 'sumber', label: expenseText.fundingSource, align: 'left', value: (row) => FUND_SOURCES[row.fund_source] ?? row.fund_source, sort: 'fund_source' },
	{ key: 'pencatat', label: termText.recordedBy, align: 'left', value: (row) => row.cashier_username ?? EMPTY_VALUE, sort: 'recorder' },
	{ key: 'jumlah', label: termText.price, value: (row) => formatRupiah(row.amount), class: () => 'font-semibold', sort: 'amount' }
];
