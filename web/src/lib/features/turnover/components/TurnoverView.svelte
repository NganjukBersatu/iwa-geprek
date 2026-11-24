<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import type { TurnoverReport, TurnoverRow, TurnoverStatus } from '$lib/api/types';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import ListSearch from '$lib/components/filter/ListSearch.svelte';
	import { noMatchText } from '$lib/components/filter/no-match';
	import Notice from '$lib/components/card/Notice.svelte';
	import SummaryCard from '$lib/components/card/SummaryCard.svelte';
	import type { Tone } from '$lib/components/card/tone';
	import Pager from '$lib/components/pager/Pager.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { formatRupiah } from '$lib/format/currency';
	import { turnoverColumns } from '../columns';
	import type { TurnoverState } from '../turnover.svelte';
	import { turnoverText } from '$lib/text/turnover';
	import { format } from '$lib/text/format';

	let { data, turnover }: { data: TurnoverReport; turnover: TurnoverState } = $props();

	const statusTone: Record<TurnoverStatus, Tone> = { out: 'danger', urgent: 'warning', dormant: 'accent', slow: 'brand', safe: 'success' };
	const urgent = (row: TurnoverRow) => row.status === 'out' || row.status === 'urgent';

	const columns = turnoverColumns;

	const matching = $derived(turnover.matching);
</script>

<div class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-4">
	<SummaryCard
		label={turnoverText.needsPurchase}
		caption={format(turnoverText.outAndUrgent, { out: data.out_count, urgent: data.urgent_count, days: data.urgent_days })}
		value="{turnover.toBuy} bahan"
		icon="shopping-cart"
		accent="primary"
	/>
	<SummaryCard label={turnoverText.idleMoney} caption={format(turnoverText.dormantIngredients, { count: data.dormant_count, days: data.dormant_days })} value={formatRupiah(data.dormant_value)} icon="moon" accent="accent" />
	<SummaryCard label={turnoverText.inventoryValue} caption={turnoverText.estimateNote} value={formatRupiah(data.total_stock_value)} icon="package" accent="ink" />
	<SummaryCard label={turnoverText.purchaseEstimate} caption={format(turnoverText.enoughForDays, { days: data.target_days })} value={formatRupiah(data.total_suggested_purchase)} icon="wallet" accent="plain" />
</div>

<Card flush>
	<CardHeader divided title={turnoverText.perIngredient} description={format(turnoverText.rowsDaysPeriod, { rows: matching.length, days: data.days, period: turnover.periodLabel })} />
	<ListSearch value={turnover.search} placeholder={turnoverText.searchPlaceholder} label={turnoverText.search} onsearch={(query) => turnover.setSearch(query)} />
	{#if matching.length === 0}
		<Notice text={noMatchText('bahan', turnover.search !== '', turnover.filters.get('kelompok_stok') !== null) ?? controlText.noIngredients} />
	{:else}
		<DataTable sort={turnover.sort} {columns} rows={turnover.pageRows} rowKey={(row) => row.ingredient_id} highlight={(row) => (urgent(row) ? 'warning' : false)} trailing="status">
			{#snippet first(row)}
				{row.name}
				{#if row.category}<span class="block text-xs font-normal text-slate-500">{row.category}</span>{/if}
			{/snippet}
			{#snippet cell(row, column)}
				{#if column.key === 'status'}
					<Badge tone={statusTone[row.status]}>{column.value(row)}</Badge>
				{:else}
					{column.value(row)}
				{/if}
			{/snippet}
		</DataTable>
		<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
			<Pager page={turnover.pageOf(matching).page} total={matching.length} unit="bahan" onchange={(page) => turnover.setPage(page)} />
		</div>
	{/if}
</Card>

<p class="text-xs text-slate-500">
	{format(turnoverText.turnoverFootnote, { days: data.days, targetDays: data.target_days, urgentDays: data.urgent_days, dormantDays: data.dormant_days, slowDays: data.slow_days })}
</p>
