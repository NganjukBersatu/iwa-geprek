<script lang="ts">
	import type { PromoReport } from '$lib/api/types';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import SummaryCard from '$lib/components/card/SummaryCard.svelte';
	import ShareBar from '$lib/components/chart/ShareBar.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { formatNumber, formatPercentPlain, formatRupiah } from '$lib/format/currency';
	import { KIND_LABELS } from '../../promotions/labels';
	import { promoUsageColumns } from '../columns';
	import type { PromoState } from '../promo.svelte';
	import { promoReportText } from '$lib/text/promo-report';
	import { format } from '$lib/text/format';

	let { data, promo }: { data: PromoReport; promo: PromoState } = $props();

	const max = $derived(Math.max(1, ...data.by_promo.map((promo) => Number(promo.total_discount))));

	const columns = promoUsageColumns;
</script>

<div class="grid grid-cols-1 gap-4 tablet:grid-cols-3">
	<SummaryCard
		label={promoReportText.promoTransactions}
		caption={format(promoReportText.ofAllValid, { percent: formatPercentPlain(data.promo_transaction_percent) })}
		value="{formatNumber(data.promo_transactions, 0)} dari {formatNumber(data.total_transactions, 0)}"
		icon="discount-2"
		accent="primary"
	/>
	<SummaryCard label={promoReportText.totalDiscount} caption={promoReportText.discountCaption} value={formatRupiah(data.total_discount)} icon="receipt-off" accent="accent" />
	<SummaryCard label={promoReportText.promoRevenue} caption={promoReportText.afterDiscount} value={formatRupiah(data.promo_transaction_revenue)} icon="wallet" accent="ink" />
</div>

<Card flush>
	<CardHeader divided title={promoReportText.perPromo} description={promo.periodLabel} />
	{#if data.by_promo.length === 0}
		<Notice text={promoReportText.noPromoTransactions} />
	{:else}
		<DataTable sort={promo.sort} {columns} rows={data.by_promo} rowKey={(row) => row.promo_id ?? row.name} trailing="potongan">
			{#snippet first(row)}
				<span class="block">
					{row.name}
					{#if row.active === false}<Badge>{promoReportText.inactive}</Badge>{/if}
				</span>
				{#if row.kind}<span class="block text-xs font-normal text-slate-500">{KIND_LABELS[row.kind] ?? row.kind}</span>{/if}
				<ShareBar value={(Number(row.total_discount) / max) * 100} tone="accent" class="mt-1.5" />
			{/snippet}
		</DataTable>
	{/if}
</Card>
