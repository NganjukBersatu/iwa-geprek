import { Filters } from '$lib/components/filter/filters.svelte';
import type { FilterDef } from '$lib/components/filter/types';
import { DATE_PRESETS, LAST_30_PRESET } from '$lib/date/range';
import { termText } from '$lib/text/terms';

export const reportPresets = [...DATE_PRESETS, LAST_30_PRESET];

export function createReportFilters(extra: FilterDef[] = []): Filters {
	return new Filters(
		[
			{ kind: 'select', key: 'cabang', label: termText.branch, options: [] },
			{ kind: 'date', key: 'rentang', label: termText.range, presets: reportPresets, reach: 'past' },
			...extra
		]
	);
}
