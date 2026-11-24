<script lang="ts">
	import MoreButton from '$lib/components/button/MoreButton.svelte';
	import ReportShell from '$lib/features/report/ReportShell.svelte';
	import StockView from '$lib/features/stock/components/StockView.svelte';
	import { stockColumns } from '$lib/features/stock/columns';
	import { StockState } from '$lib/features/stock/stock.svelte';
	import { pageText } from '$lib/text/pages';

	const stock = new StockState();
</script>

<ReportShell report={stock} title={pageText.ingredientStockTitle} description={pageText.ingredientStockDescription}>
	{#snippet extra()}
		<MoreButton exporter={{ title: pageText.exportTitles.ingredientStock, columns: stockColumns, rows: async () => stock.rows }} />
	{/snippet}
	{#snippet children(data)}
		<StockView {data} {stock} />
	{/snippet}
</ReportShell>
