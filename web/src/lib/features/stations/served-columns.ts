import { controlText } from '$lib/text/controls';
import { QUIET_VALUE } from '$lib/components/table/quiet-value';
import type { KitchenHour, KitchenOrder } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { EMPTY_VALUE, formatNumber } from '$lib/format/currency';
import { formatDateTime } from '$lib/format/datetime';
import { termText } from '$lib/text/terms';
import { stationText } from '$lib/text/stations';
import { format } from '$lib/text/format';

export const minutes = (value: string | null) => (value === null ? EMPTY_VALUE : format(controlText.minutesCount, { count: formatNumber(value, 1) }));
export const hour = (value: number) => `${String(value).padStart(2, '0')}.00`;

export function hourColumns(late: (row: KitchenHour) => boolean): Column<KitchenHour>[] {
	return [
		{ key: 'jam', label: termText.hour, value: (row) => hour(row.hour), sort: 'hour' },
		{ key: 'jumlah', label: termText.order, value: (row) => formatNumber(row.count, 0), sort: 'count' },
		{ key: 'rata', label: stationText.average, value: (row) => minutes(row.average_minutes), class: (row) => (late(row) ? 'font-semibold text-danger-700' : 'font-semibold'), sort: 'average' },
		{ key: 'terlambat', label: stationText.late, value: (row) => formatNumber(row.late, 0), class: (row) => (row.late > 0 ? 'font-semibold text-danger-700' : QUIET_VALUE), sort: 'late' }
	];
}

export const orderColumns: Column<KitchenOrder>[] = [
	{ key: 'pesanan', label: termText.order, align: 'left', value: (row) => `${row.customer_name || stationText.unnamed}${row.table_no ? ` · Meja ${row.table_no}` : ''}`, sort: 'order' },
	{ key: 'item', label: termText.item, align: 'left', value: (row) => row.items_summary, sort: 'items' },
	{ key: 'masuk', label: stationText.entered, align: 'left', value: (row) => formatDateTime(row.created_at), sort: 'created_at' },
	{ key: 'selesai', label: stationText.finished, align: 'left', value: (row) => formatDateTime(row.served_at), sort: 'served_at' },
	{ key: 'menit', label: stationText.duration, value: (row) => minutes(row.minutes), sort: 'minutes' }
];
