<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import Banner from '$lib/components/card/Banner.svelte';
	import SummaryBadge from '$lib/components/card/SummaryBadge.svelte';
	import SummaryCard from '$lib/components/card/SummaryCard.svelte';
	import { formatNumber, formatPercentPlain, formatRupiah } from '$lib/format/currency';
	import type { ProductPeakState } from '../peak.svelte';
	import { productPeakText } from '$lib/text/product-peak';
	import { format } from '$lib/text/format';
	import RichText from '$lib/components/text/RichText.svelte';

	let { peak }: { peak: ProductPeakState } = $props();

	const data = $derived(peak.data);
	const busiest = $derived(peak.unitHighlight);
	const concentrated = $derived(Number(data?.top_product_percent ?? 0) > 30);
</script>

{#if data}
	<div class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
		<Banner tone={concentrated ? 'warning' : 'brand'} icon="trophy" title={format(productPeakText.topProduct, { name: data.top_product ?? '—' })}>
			<RichText template={productPeakText.topProductShare} values={{ percent: formatPercentPlain(data.top_product_percent) }} />
			{#if concentrated}{productPeakText.concentrationNote}{/if}
		</Banner>
		{#if busiest?.peak_label}
			<Banner tone="accent" icon="clock" title={format(productPeakText.mostSold, { unit: peak.unitName, label: busiest.peak_label })}>
				<RichText template={productPeakText.averageItemsShare} values={{ items: formatNumber(busiest.peak_value, 1), percent: formatPercentPlain(busiest.peak_percent) }} />
			</Banner>
		{/if}
		<SummaryCard
			label={productPeakText.periodScope}
			caption={format(productPeakText.itemsAndReceipts, { items: formatNumber(data.total_qty, 0), receipts: formatNumber(data.total_transactions, 0) })}
			value={format(controlText.productsCount, { count: data.product_count })}
			icon="package"
			accent="primary"
		>
			{#snippet aside()}<SummaryBadge accent="primary">{formatRupiah(data.total_revenue)}</SummaryBadge>{/snippet}
		</SummaryCard>
	</div>
{/if}
