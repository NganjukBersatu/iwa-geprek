<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import type { MarginReport } from '$lib/api/types';
	import Badge from '$lib/components/card/Badge.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import ListSearch from '$lib/components/filter/ListSearch.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import OrdersWithoutLinesNotice from '$lib/features/report/OrdersWithoutLinesNotice.svelte';
	import SummaryCard from '$lib/components/card/SummaryCard.svelte';
	import DumbbellChart from '$lib/components/chart/DumbbellChart.svelte';
	import Pager from '$lib/components/pager/Pager.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { formatPercentOrDash, formatPercentPlain, formatRupiahOrDash } from '$lib/format/currency';
	import { marginColumns } from '../columns';
	import type { MarginState } from '../margin.svelte';
	import { termText } from '$lib/text/terms';
	import { marginText } from '$lib/text/margin';
	import { format } from '$lib/text/format';

	let { data, margin }: { data: MarginReport; margin: MarginState } = $props();

	const columns = marginColumns;

	const matching = $derived(margin.matching);
</script>

<OrdersWithoutLinesNotice count={data.orders_without_lines} revenue={data.revenue_without_lines} />
<div class="grid grid-cols-1 gap-4 tablet:grid-cols-3">
	<SummaryCard label={termText.revenue} caption={marginText.afterDiscount} value={formatRupiahOrDash(data.total_revenue)} icon="wallet" accent="primary" />
	<SummaryCard label={marginText.cost} caption={marginText.priceAtTransaction} value={formatRupiahOrDash(data.total_cost)} icon="package" accent="accent" />
	<SummaryCard label={marginText.grossProfit} caption={marginText.revenueMinusCost} value={formatRupiahOrDash(data.total_margin)} icon="trending-up" accent="ink" />
</div>

{#if data.menus_without_cost > 0}
	<Banner tone="warning" icon="alert-triangle" title={format(marginText.menusWithoutCost, { count: data.menus_without_cost })}>
		{marginText.partialCostWarning}
	</Banner>
{/if}

{#if data.items.length === 0}
	<Card><Notice class="px-0!" title={marginText.noTransactions} text={marginText.noTransactionsHint} /></Card>
{:else}
	<Card>
		<CardHeader class="mb-4" title={marginText.topMenusTitle} description={marginText.chartLegend} />
		<DumbbellChart
			rows={data.top.map((item) => ({
				label: item.menu_item_name,
				from: Number(item.cost ?? 0),
				to: Number(item.revenue),
				note: item.margin_percent === null ? '' : formatPercentPlain(item.margin_percent),
				detail: `Omzet ${formatRupiahOrDash(item.revenue)}<br/>Modal ${formatRupiahOrDash(item.cost)}<br/>Laba <b>${formatRupiahOrDash(item.margin)}</b>${item.margin_percent === null ? '' : ` (${formatPercentOrDash(item.margin_percent)})`}`
			}))}
			fromName="Modal"
			toName="Omzet"
			label={marginText.chartSummary}
		/>
	</Card>

	<Card flush>
		<CardHeader divided title={marginText.allMenus} description={format(marginText.menusCaption, { count: matching.length, total: margin.search ? ` dari ${data.items.length}` : '', period: margin.periodLabel })} />
		<ListSearch value={margin.search} placeholder={marginText.searchPlaceholder} label={controlText.searchMenu} onsearch={(query) => margin.setSearch(query)} />
		{#if matching.length === 0}
			<Notice text={marginText.noMatch} />
		{:else}
			<DataTable sort={margin.sort} {columns} rows={margin.pageRows} rowKey={(row) => row.menu_item_name} trailing="laba">
				{#snippet first(row)}
					{row.menu_item_name}
					{#if !row.cost_complete && row.cost !== null}<Badge tone="warning">{marginText.partialCost}</Badge>{/if}
				{/snippet}
			</DataTable>
			<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
				<Pager page={margin.pageOf(matching).page} total={matching.length} unit="menu" onchange={(page) => margin.setPage(page)} />
			</div>
		{/if}
	</Card>

	<p class="text-xs text-slate-500">
		{marginText.footnote}
	</p>
{/if}
