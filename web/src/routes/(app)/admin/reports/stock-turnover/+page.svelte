<script lang="ts">
	import MoreButton from '$lib/components/button/MoreButton.svelte';
	import ReportShell from '$lib/features/report/ReportShell.svelte';
	import TurnoverView from '$lib/features/turnover/components/TurnoverView.svelte';
	import { turnoverColumns } from '$lib/features/turnover/columns';
	import { TurnoverState } from '$lib/features/turnover/turnover.svelte';
	import { pageText } from '$lib/text/pages';

	const turnover = new TurnoverState();
</script>

<ReportShell report={turnover} title={pageText.turnoverTitle} description={pageText.turnoverDescription}>
	{#snippet extra()}
		<MoreButton exporter={{ title: pageText.exportTitles.stockTurnover, columns: turnoverColumns, rows: async () => turnover.matching }} />
	{/snippet}
	{#snippet children(data)}
		<TurnoverView {data} {turnover} />
	{/snippet}
</ReportShell>
