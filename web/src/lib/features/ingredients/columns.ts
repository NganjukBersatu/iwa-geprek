import type { Ingredient } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { EMPTY_VALUE, formatNumber, formatRupiah } from '$lib/format/currency';
import { termText } from '$lib/text/terms';
import { ingredientText } from '$lib/text/ingredients';

export const ingredientColumns: Column<Ingredient>[] = [
	{ key: 'bahan', label: termText.ingredient, align: 'left', value: (row) => row.name, sort: 'name' },
	{ key: 'kategori', label: termText.category, align: 'left', value: (row) => row.category ?? EMPTY_VALUE, sort: 'category' },
	{ key: 'saldo', label: ingredientText.balance, value: (row) => `${formatNumber(row.balance)} ${row.unit}`, sort: 'balance' },
	{ key: 'harga', label: ingredientText.unitPrice, value: (row) => formatRupiah(row.unit_price), sort: 'unit_price' },
	{ key: 'status', label: termText.status, align: 'left', value: (row) => (row.is_active ? termText.active : termText.inactive), sort: 'active' }
];
