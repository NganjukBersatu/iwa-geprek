import type { IngredientCountRequest } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { formatDate } from '$lib/date/range';
import { EMPTY_VALUE, formatNumber } from '$lib/format/currency';
import { formatDateTime } from '$lib/format/datetime';
import { ingredientCountRequestText as text } from '$lib/text/ingredient-count-requests';
import { format } from '$lib/text/format';

export const pendingRequestColumns: Column<IngredientCountRequest>[] = [
	{ key: 'periode', label: text.columns.period, align: 'left', value: (row) => format(text.periodRange, { from: formatDate(row.close_start), to: formatDate(row.close_end) }) },
	{ key: 'cabang', label: text.columns.branch, align: 'left', value: (row) => row.outlet_name },
	{ key: 'stok_awal', label: text.columns.opening, align: 'left', value: (row) => format(text.openingOf, { filled: formatNumber(row.opening_filled, 0), total: formatNumber(row.opening_total, 0) }) },
	{ key: 'diajukan', label: text.columns.requested, align: 'left', value: (row) => format(text.requestedBy, { name: row.requested_by ?? EMPTY_VALUE, time: formatDateTime(row.created_at) }) },
	{ key: 'catatan', label: text.columns.note, align: 'left', value: (row) => row.note ?? EMPTY_VALUE }
];
