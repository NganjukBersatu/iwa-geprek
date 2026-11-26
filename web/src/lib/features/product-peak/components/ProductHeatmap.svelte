<script lang="ts">
	import Button from '$lib/components/button/Button.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import HeatmapChart from '$lib/components/chart/HeatmapChart.svelte';
	import { formatNumber, formatRupiah } from '$lib/format/currency';
	import { hourLabel } from '../../sales-peak/filters';
	import type { ProductPeakState } from '../peak.svelte';
	import { productPeakText } from '$lib/text/product-peak';
	import { format } from '$lib/text/format';

	let { peak }: { peak: ProductPeakState } = $props();

	const unitLower = $derived(peak.unitName.toLowerCase());
</script>

{#if peak.data}
	<Card>
		<CardHeader
			class="mb-4"
			title={peak.diving ? format(productPeakText.hourPerMinute, { hour: hourLabel(peak.data.focus_hour ?? 0) }) : format(productPeakText.itemsSoldPer, { unit: unitLower })}
			description={format(productPeakText.heatmapCaption, { count: peak.data.series.length, search: peak.search ? ` · disaring \"${peak.search}\"` : '' })}
		>
			{#snippet actions()}
				{#if peak.diving}
					<Button label={productPeakText.backToAllHours} icon="arrow-left" onclick={() => peak.leave()} />
				{/if}
			{/snippet}
		</CardHeader>

		{#if peak.data.series.length === 0}
			<Notice text={peak.search ? productPeakText.noMatch : productPeakText.noSales} />
		{:else}
			<HeatmapChart
				columns={peak.data.slots.map((slot) => slot.label)}
				rows={peak.visibleSeries.map((series) => ({ label: series.menu_item_name, values: series.values }))}
				label={format(productPeakText.heatmapSummary, { unit: unitLower })}
			/>

			<ul class="mt-3 grid grid-cols-2 gap-2 tablet:grid-cols-3 laptop:grid-cols-5">
				{#each peak.data.series as series (series.menu_item_name)}
					{@const off = peak.hidden.has(series.menu_item_name)}
					<li>
						<button
							type="button"
							onclick={() => peak.toggleSeries(series.menu_item_name)}
							aria-pressed={!off}
							title={off ? productPeakText.showRow : productPeakText.hideRow}
							class="flex w-full min-w-0 flex-col rounded-lg border px-2.5 py-2 text-left transition-colors motion-reduce:transition-none {off
								? 'border-slate-100 bg-slate-50 opacity-60'
								: 'border-brand-tint bg-white hover:border-brand hover:bg-brand-soft'}"
						>
							<span class="line-clamp-2 text-xs font-semibold text-slate-700 wrap-break-word" title={series.menu_item_name}>{series.menu_item_name}</span>
							<span class="text-xs text-slate-500">{format(productPeakText.itemsAndRevenue, { items: formatNumber(series.total_qty, 0), revenue: formatRupiah(series.total_revenue) })}</span>
						</button>
					</li>
				{/each}
			</ul>
		{/if}
	</Card>
{/if}
