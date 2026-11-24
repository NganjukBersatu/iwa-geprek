import type { StationRoute } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { EMPTY_VALUE } from '$lib/format/currency';
import { printerText as text } from '$lib/text/printers';
import { printedAt, ROUTE_LOOKS, shownOn } from './printers.svelte';

type RouteRow = StationRoute & { id: string };

export const routeColumns: Column<RouteRow>[] = [
	{ key: 'station', label: text.columns.station, align: 'left', value: (row) => row.station_name },
	{ key: 'tablet', label: text.columns.tablet, align: 'left', value: (row) => shownOn(row) },
	{ key: 'category', label: text.columns.category, align: 'left', value: (row) => (row.category_names.length > 0 ? row.category_names.join(', ') : EMPTY_VALUE) },
	{ key: 'printedAt', label: text.columns.printedAt, align: 'left', value: (row) => printedAt(row) },
	{ key: 'status', label: text.columns.status, align: 'left', value: (row) => ROUTE_LOOKS[row.state].label }
];
