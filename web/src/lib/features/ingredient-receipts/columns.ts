import type { IngredientMovement } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { formatDate } from '$lib/date/range';
import { EMPTY_VALUE, formatNumber } from '$lib/format/currency';
import { formatDateTime } from '$lib/format/datetime';
import { termText } from '$lib/text/terms';

export const receiptColumns: Column<IngredientMovement>[] = [
	{ key: 'bahan', label: termText.ingredient, align: 'left', value: (row) => row.ingredient_name, sort: 'ingredient' },
	{ key: 'hari', label: termText.day, align: 'left', value: (row) => formatDate(row.business_day), sort: 'business_day' },
	{ key: 'waktu', label: termText.recordedAt, align: 'left', value: (row) => formatDateTime(row.created_at), sort: 'created_at' },
	{ key: 'pencatat', label: termText.recordedBy, align: 'left', value: (row) => row.user_name ?? EMPTY_VALUE, sort: 'user' },
	{ key: 'jumlah', label: termText.quantity, value: (row) => `${formatNumber(row.qty)} ${row.unit}`, class: () => 'font-semibold', sort: 'qty' }
];
