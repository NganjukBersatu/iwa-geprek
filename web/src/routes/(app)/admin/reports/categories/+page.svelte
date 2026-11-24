<script lang="ts">
	import SummaryCard from '$lib/components/card/SummaryCard.svelte';
	import { formatNumber, formatRupiah } from '$lib/format/currency';
	import { CategoryState } from '$lib/features/category/category.svelte';
	import CategoryTable from '$lib/features/category/components/CategoryTable.svelte';
	import UnsoldList from '$lib/features/category/components/UnsoldList.svelte';
	import OrdersWithoutLinesNotice from '$lib/features/report/OrdersWithoutLinesNotice.svelte';
	import ReportShell from '$lib/features/report/ReportShell.svelte';
	import { pageText } from '$lib/text/pages';
	import { format } from '$lib/text/format';

	const category = new CategoryState();
</script>

<ReportShell report={category} title={pageText.categoriesReportTitle} description={pageText.categoriesReportDescription}>
	{#snippet children(data)}
		<OrdersWithoutLinesNotice count={data.orders_without_lines} revenue={data.revenue_without_lines} />
		<div class="grid grid-cols-1 gap-4 tablet:grid-cols-3">
			<SummaryCard label={pageText.totalRevenue} caption={format(pageText.categoriesCount, { count: data.categories.length })} value={formatRupiah(data.total_revenue)} icon="wallet" accent="primary" />
			<SummaryCard label={pageText.menusSold} caption={format(pageText.ofMenus, { count: formatNumber(data.total_menu_count, 0) })} value={formatNumber(data.sold_menu_count, 0)} icon="shopping-cart" accent="accent" />
			<SummaryCard label={pageText.unsold} caption={pageText.menusWithoutSales} value={formatNumber(data.unsold.length, 0)} icon="alert-triangle" accent="ink" />
		</div>

		<div class="grid grid-cols-1 gap-4 laptop:grid-cols-2 tablet:gap-6">
			<CategoryTable {category} />
			<UnsoldList {category} />
		</div>
	{/snippet}
</ReportShell>
