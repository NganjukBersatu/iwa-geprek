<script lang="ts">
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Chart from '$lib/components/chart/Chart.svelte';
	import { axisTooltip, barSeries, baseChartOptions, chartPalette } from '$lib/charts/theme';
	import { formatRupiah } from '$lib/format/currency';
	import type { DashboardState } from '../dashboard.svelte';
	import { termText } from '$lib/text/terms';
	import { dashboardCardText } from '$lib/text/dashboard-cards';
	import { format } from '$lib/text/format';

	let { dashboard }: { dashboard: DashboardState } = $props();

	const empty = $derived(dashboard.chartRows.every((row) => row.income === 0 && row.expense === 0));

	const options = $derived.by(() => {
		const base = baseChartOptions();
		const rows = dashboard.chartRows;
		return {
			...base,
			xAxis: { ...base.xAxis, data: rows.map((row) => row.label) },
			series: [
				barSeries(termText.income, rows.map((row) => row.income), chartPalette.income),
				barSeries(termText.expense, rows.map((row) => row.expense), chartPalette.expense)
			],
			tooltip: { ...base.tooltip, formatter: axisTooltip(formatRupiah) }
		};
	});
</script>

<Card>
	<CardHeader class="mb-4" title={dashboardCardText.incomeVersusExpense} description="{dashboard.periodLabel} · {dashboard.unitLabel}" />
	<Chart {options} {empty} class="h-56 tablet:h-64 laptop:h-80" label={format(dashboardCardText.trendChartSummary, { unit: dashboard.unitLabel })} />
</Card>
