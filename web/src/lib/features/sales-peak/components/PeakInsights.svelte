<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import Banner from '$lib/components/card/Banner.svelte';
	import SummaryCard from '$lib/components/card/SummaryCard.svelte';
	import { formatNumber, formatPercentPlain, formatRupiah } from '$lib/format/currency';
	import type { SalesPeakState } from '../peak.svelte';
	import { termText } from '$lib/text/terms';
	import { salesPeakText } from '$lib/text/sales-peak';
	import { format } from '$lib/text/format';
	import RichText from '$lib/components/text/RichText.svelte';

	let { peak }: { peak: SalesPeakState } = $props();

	const data = $derived(peak.data);
	const sales = $derived(peak.salesHighlight);
	const traffic = $derived(peak.trafficHighlight);
	const unit = $derived(peak.unitName);
	const unitLower = $derived(unit.toLowerCase());
</script>

{#if data}
	<div class="grid grid-cols-1 gap-4 laptop:grid-cols-2">
		{#if sales?.peak_label}
			<Banner tone="brand" icon="trophy" title={format(salesPeakText.mostRevenue, { unit: unit, label: sales.peak_label })}>
				<RichText template={salesPeakText.peakSalesShare} values={{ amount: formatRupiah(sales.peak_value), unit: unitLower, percent: formatPercentPlain(sales.peak_percent) }} />
				{#if sales.ratio}
					<RichText template={salesPeakText.peakRatio} values={{ ratio: formatNumber(sales.ratio, 1), unit: unitLower, quiet: sales.quiet_label ?? '' }} />
				{:else if sales.quiet_label}
					{format(salesPeakText.quietProducesNothing, { unit: unitLower, label: sales.quiet_label })}
				{/if}
			</Banner>
		{/if}
		{#if traffic?.peak_label}
			<Banner tone={peak.peaksDiffer ? 'accent' : 'neutral'} icon="users" title={format(salesPeakText.busiest, { unit: unit, label: traffic.peak_label })}>
				<RichText template={salesPeakText.averageReceiptsShare} values={{ receipts: formatNumber(traffic.peak_value, 1), percent: formatPercentPlain(traffic.peak_percent) }} />
				{#if peak.peaksDiffer}
					<RichText template={salesPeakText.peakDifferent} values={{ unit: unitLower }} />
				{/if}
			</Banner>
		{/if}
	</div>

	<div class="grid grid-cols-1 gap-4 tablet:grid-cols-3 laptop:grid-cols-5">
		<SummaryCard label={salesPeakText.totalSales} caption={format(controlText.daysCount, { count: data.days })} value={formatRupiah(data.total_sales)} icon="wallet" accent="primary" />
		<SummaryCard label={termText.transaction} caption={salesPeakText.receiptsInPeriod} value={formatNumber(data.total_transactions, 0)} icon="receipt" accent="accent" />
		<SummaryCard label={salesPeakText.itemsSold} caption={salesPeakText.productCount} value={formatNumber(data.total_products, 0)} icon="shopping-cart" accent="ink" />
		<SummaryCard label={salesPeakText.averageReceiptValue} caption={salesPeakText.perTransaction} value={formatRupiah(data.average_per_transaction)} icon="calculator" accent="plain" />
		<SummaryCard label={salesPeakText.registeredCustomers} caption={format(salesPeakText.receiptsWithoutName, { count: formatNumber(data.transactions_without_customer, 0) })} value={formatNumber(data.total_customers, 0)} icon="user-check" accent="plain" />
	</div>
{/if}
