<script lang="ts">
	import { termText } from '$lib/text/terms';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import SeriesChart from '$lib/components/chart/SeriesChart.svelte';
	import { chartPalette } from '$lib/charts/theme';
	import { formatDayMonth } from '$lib/date/range';
	import { formatRupiah } from '$lib/format/currency';
	import type { OverviewState } from '../overview.svelte';
	import { financeText } from '$lib/text/finance';
	import { format } from '$lib/text/format';

	let { overview }: { overview: OverviewState } = $props();

	const rows = $derived(overview.rows);
</script>

<Card>
	<CardHeader class="mb-4" title={financeText.patternPerDate} description={format(financeText.overviewChartCaption, { period: overview.periodLabel })} />
	<SeriesChart
		labels={rows.map((row) => formatDayMonth(row.date))}
		series={[
			{ name: termText.income, values: rows.map((row) => Number(row.income_total)), color: chartPalette.income },
			{ name: termText.expense, values: rows.map((row) => Number(row.expense_total)), color: chartPalette.expense },
			{ name: termText.profit, values: rows.map((row) => Number(row.profit_total)), color: chartPalette.profit, kind: 'line' }
		]}
		tooltipFormat={formatRupiah}
		class="h-60 tablet:h-72 laptop:h-80"
		label={financeText.chartSummary}
	/>
</Card>
