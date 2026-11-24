<script lang="ts">
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import SummaryCard from '$lib/components/card/SummaryCard.svelte';
	import ShareBar from '$lib/components/chart/ShareBar.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { formatNumber, formatPercentPlain, formatRupiah } from '$lib/format/currency';
	import { extraColumns } from '../columns';
	import type { VariantState } from '../variant.svelte';
	import { variantReportText } from '$lib/text/variant-report';
	import { format } from '$lib/text/format';

	let { variant }: { variant: VariantState } = $props();

	const extras = $derived(variant.extras);

	const columns = extraColumns;
</script>

{#if extras}
	<div class="grid grid-cols-1 gap-4 tablet:grid-cols-3">
		<SummaryCard label={variantReportText.extraRevenue} caption={variantReportText.priceWhenSold} value={formatRupiah(extras.total_extra_revenue)} icon="wallet" accent="primary" />
		<SummaryCard label={variantReportText.revenueShare} caption={format(variantReportText.ofTotalRevenue, { amount: formatRupiah(extras.total_revenue) })} value={formatPercentPlain(extras.revenue_percent)} icon="percentage" accent="ink" />
		<SummaryCard label={variantReportText.extrasSold} caption={format(variantReportText.extrasKinds, { count: extras.rows.length })} value={formatNumber(extras.total_quantity, 0)} icon="plus" accent="accent" />
	</div>

	{#if extras.rows.length === 0}
		<Card><Notice class="px-0!" title={variantReportText.noExtrasSold} text={variantReportText.noExtrasSoldHint} /></Card>
	{:else}
		<Card flush>
			<CardHeader divided title={variantReportText.perExtra} description={variant.periodLabel} />
			<DataTable sort={variant.extraSort} {columns} rows={extras.rows} rowKey={(row) => row.extra} trailing="pendapatan">
				{#snippet cell(row, column)}
					{#if column.key === 'persen'}
						<span class="flex items-center gap-2">
							<ShareBar value={Number(row.revenue_percent)} class="w-20 shrink-0" />
							<span class="text-slate-500">{column.value(row)}</span>
						</span>
					{:else}
						{column.value(row)}
					{/if}
				{/snippet}
			</DataTable>
		</Card>
		<p class="text-xs text-slate-500">
			{variantReportText.extrasNote}
		</p>
	{/if}
{/if}
