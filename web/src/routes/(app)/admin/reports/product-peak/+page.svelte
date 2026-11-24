<script lang="ts">
	import MoreButton from '$lib/components/button/MoreButton.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import ListSearch from '$lib/components/filter/ListSearch.svelte';
	import ProductHeatmap from '$lib/features/product-peak/components/ProductHeatmap.svelte';
	import ProductInsights from '$lib/features/product-peak/components/ProductInsights.svelte';
	import ProductTable from '$lib/features/product-peak/components/ProductTable.svelte';
	import { productPeakColumns } from '$lib/features/product-peak/columns';
	import { ProductPeakState } from '$lib/features/product-peak/peak.svelte';
	import OrdersWithoutLinesNotice from '$lib/features/report/OrdersWithoutLinesNotice.svelte';
	import ReportShell from '$lib/features/report/ReportShell.svelte';
	import { pageText } from '$lib/text/pages';

	const peak = new ProductPeakState();
</script>

<ReportShell report={peak} title={pageText.productPeakTitle} description={pageText.productPeakDescription}>
	{#snippet extra()}
		<MoreButton exporter={{ title: pageText.exportTitles.productPeak, columns: productPeakColumns(peak.unitName), rows: () => peak.exportRows() }} />
	{/snippet}
	{#snippet children(data)}
		<OrdersWithoutLinesNotice count={data.orders_without_lines} revenue={data.revenue_without_lines} />
		{#if data.total_qty === 0}
			<Notice title={pageText.noSales} text={pageText.noProductSalesHint} />
		{:else}
			<Card flush>
				<ListSearch value={peak.search} placeholder={pageText.searchProductPlaceholder} label={pageText.searchProduct} divided={false} onsearch={(query) => peak.setSearch(query)} />
			</Card>
			<ProductInsights {peak} />
			<ProductHeatmap {peak} />
			<ProductTable {peak} />
		{/if}
	{/snippet}
</ReportShell>
