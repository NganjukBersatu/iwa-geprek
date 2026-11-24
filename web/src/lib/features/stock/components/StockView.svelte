<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import type { StockReport } from '$lib/api/types';
	import PageButton from '$lib/components/button/PageButton.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import ListSearch from '$lib/components/filter/ListSearch.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import SummaryCard from '$lib/components/card/SummaryCard.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { formatRupiahOrDash } from '$lib/format/currency';
	import { PAGES } from '$lib/nav/pages';
	import { stockColumns } from '../columns';
	import { REPLACEMENT } from '../labels';
	import type { StockState } from '../stock.svelte';
	import { stockReportText } from '$lib/text/stock-report';
	import { format } from '$lib/text/format';

	let { data, stock }: { data: StockReport; stock: StockState } = $props();

	const columns = stockColumns;

	const rows = $derived(stock.rows);
</script>

<div class="grid grid-cols-1 gap-4 tablet:grid-cols-3">
	<SummaryCard label={stockReportText.totalReimbursement} caption={stockReportText.overToleranceBilled} value={formatRupiahOrDash(data.total_replacement)} icon="receipt-2" accent="primary" />
	<SummaryCard label={stockReportText.totalToleranceValue} caption={stockReportText.withinToleranceAbsorbed} value={formatRupiahOrDash(data.total_tolerated_value)} icon="scale" accent="accent" />
	<SummaryCard label={stockReportText.needsReview} caption={stockReportText.negativeClosingNote} value="{data.check_count} bahan" icon="alert-triangle" accent="ink" />
</div>

{#if data.count_id === null}
	<Banner tone="accent" icon="info-circle">
		{stockReportText.notCountedYet}
		{#snippet action()}
			<PageButton page={PAGES.ingredientCounts} icon="clipboard-check" />
		{/snippet}
	</Banner>
{/if}

<Card flush>
	<CardHeader
		divided
		title={stockReportText.listTitle}
		description={format(stockReportText.ingredientsCaptionPeriod, { count: rows.length, total: stock.search ? ` dari ${data.rows.length}` : '', period: stock.periodLabel })}
	/>
	<ListSearch value={stock.search} placeholder={stockReportText.searchPlaceholder} label={stockReportText.search} onsearch={(query) => stock.setSearch(query)} />
	{#if rows.length === 0}
		<Notice text={data.rows.length === 0 ? controlText.noIngredients : stockReportText.noMatch} />
	{:else}
		<DataTable sort={stock.sort} {columns} {rows} rowKey={(row) => row.ingredient_id} highlight={(row) => (row.replacement_status === 'check' ? 'warning' : false)} trailing="stok_akhir">
			{#snippet cell(row, column)}
				{#if column.key === 'status'}
					{@const status = REPLACEMENT[row.replacement_status]}
					{#if status.tone === 'muted'}
						<span class="text-slate-500">{status.label}</span>
					{:else}
						<Badge tone={status.tone}>{status.label}</Badge>
					{/if}
				{:else}
					{column.value(row)}
				{/if}
			{/snippet}
		</DataTable>
	{/if}
</Card>

<p class="text-xs text-slate-500">
	{stockReportText.formulaNote}
</p>
