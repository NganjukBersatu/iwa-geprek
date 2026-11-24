import type { Filters } from '$lib/components/filter/filters.svelte';
import type { DatePreset } from '$lib/date/range';
import { createReportFilters } from '../report/filters';
import { termText } from '$lib/text/terms';
import { dashboardCardText } from '$lib/text/dashboard-cards';

export const periodOptions = [
	{ value: 'daily', label: dashboardCardText.daily },
	{ value: 'weekly', label: dashboardCardText.weekly },
	{ value: 'monthly', label: dashboardCardText.monthly }
];

export const comparePresets: DatePreset[] = [
	{ value: 'auto', label: dashboardCardText.compareAutomatic },
	{ value: 'week', label: dashboardCardText.compareLastWeek },
	{ value: 'month', label: dashboardCardText.compareLastMonth },
	{ value: 'year', label: dashboardCardText.compareLastYear }
];

export function createDashboardFilters(): Filters {
	return createReportFilters(
		[
			{ kind: 'select', key: 'periode', label: termText.period, options: periodOptions, empty: 'daily', requires: { key: 'rentang', value: null } },
			{ kind: 'date', key: 'bandingkan', label: dashboardCardText.compare, presets: comparePresets, reach: 'past' }
		]
	);
}
