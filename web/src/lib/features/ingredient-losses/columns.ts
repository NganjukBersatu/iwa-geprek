import type { IngredientMovement } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { formatDate } from '$lib/date/range';
import { EMPTY_VALUE, formatNumber } from '$lib/format/currency';
import { formatDateTime } from '$lib/format/datetime';
import { USE, WASTE } from './kinds';
import { termText } from '$lib/text/terms';
import { ingredientLossText } from '$lib/text/ingredient-losses';

export const lossColumns = (kind: string): Column<IngredientMovement>[] => [
	{ key: 'bahan', label: termText.ingredient, align: 'left', value: (row) => row.ingredient_name, sort: 'ingredient' },
	{ key: 'hari', label: termText.day, align: 'left', value: (row) => formatDate(row.business_day), sort: 'business_day' },
	{ key: 'waktu', label: termText.recordedAt, align: 'left', value: (row) => formatDateTime(row.created_at), sort: 'created_at' },
	{ key: 'jumlah', label: termText.quantity, value: (row) => `${formatNumber(Math.abs(Number(row.qty)))} ${row.unit}`, sort: 'qty' },
	...(kind === WASTE || kind === USE ? [{ key: 'sebab', label: ingredientLossText.cause, align: 'left' as const, value: (row: IngredientMovement) => row.cause_label ?? EMPTY_VALUE, sort: 'cause' }] : []),
	{ key: 'pencatat', label: termText.recordedBy, align: 'left', value: (row) => row.user_name ?? EMPTY_VALUE, sort: 'user' }
];
