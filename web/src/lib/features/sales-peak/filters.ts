import type { FilterDef } from '$lib/components/filter/types';
import { termText } from '$lib/text/terms';
import { salesPeakText } from '$lib/text/sales-peak';
import { format } from '$lib/text/format';

export const unitOptions = [
	{ value: 'hour', label: termText.hour },
	{ value: 'weekday', label: termText.day },
	{ value: 'date', label: termText.date },
	{ value: 'month', label: salesPeakText.month }
];

export const metricOptions = [
	{ value: 'sales', label: salesPeakText.sales },
	{ value: 'transactions', label: termText.transaction }
];

export const hourLabel = (hour: number) => `${String(hour).padStart(2, '0')}:00`;

export const hourOptions = Array.from({ length: 24 }, (_, hour) => ({ value: String(hour), label: format(salesPeakText.hourPerMinuteShort, { hour: hourLabel(hour) }) }));

export const timeUnitFilters: FilterDef[] = [
	{ kind: 'select', key: 'satuan', label: salesPeakText.viewBy, options: unitOptions, empty: 'hour' },
	{ kind: 'select', key: 'jam', label: salesPeakText.hourDetails, options: hourOptions, requires: { key: 'satuan', value: 'hour' } }
];
