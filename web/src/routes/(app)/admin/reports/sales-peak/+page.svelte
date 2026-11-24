<script lang="ts">
	import MoreButton from '$lib/components/button/MoreButton.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import ReportShell from '$lib/features/report/ReportShell.svelte';
	import PeakCharts from '$lib/features/sales-peak/components/PeakCharts.svelte';
	import PeakInsights from '$lib/features/sales-peak/components/PeakInsights.svelte';
	import PeakTable from '$lib/features/sales-peak/components/PeakTable.svelte';
	import { peakColumns } from '$lib/features/sales-peak/columns';
	import { SalesPeakState } from '$lib/features/sales-peak/peak.svelte';
	import { pageText } from '$lib/text/pages';

	const peak = new SalesPeakState();
</script>

<ReportShell report={peak} title={pageText.salesPeakTitle} description={pageText.salesPeakDescription}>
	{#snippet extra()}
		<MoreButton exporter={{ title: pageText.exportTitles.salesPeak, columns: peakColumns(peak.unitName), rows: async () => peak.data?.rows ?? [] }} />
	{/snippet}
	{#snippet children(data)}
		{#if data.total_transactions === 0}
			<Notice title={pageText.noSales} text={pageText.noTransactionsHint} />
		{:else}
			<PeakInsights {peak} />
			<PeakCharts {peak} />
			<PeakTable {peak} />
		{/if}
	{/snippet}
</ReportShell>
