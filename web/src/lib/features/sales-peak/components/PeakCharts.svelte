<script lang="ts">
	import { dynamicStyle } from '$lib/motion/actions';
	import Button from '$lib/components/button/Button.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import SeriesChart from '$lib/components/chart/SeriesChart.svelte';
	import { chartPalette } from '$lib/charts/theme';
	import { formatNumber, formatRupiah, formatRupiahShort } from '$lib/format/currency';
	import { metricOptions } from '../filters';
	import type { PeakMetric, SalesPeakState } from '../peak.svelte';
	import { salesPeakText } from '$lib/text/sales-peak';
	import { format } from '$lib/text/format';

	let { peak }: { peak: SalesPeakState } = $props();

	const colors: Record<PeakMetric, string> = { sales: chartPalette.income, transactions: chartPalette.profit };
	const names = Object.fromEntries(metricOptions.map((option) => [option.value, option.label])) as Record<PeakMetric, string>;
	const suffix: Record<PeakMetric, string> = { sales: '', transactions: ' transaksi' };

	const unitLower = $derived(peak.unitName.toLowerCase());
	const canDive = $derived(peak.query.unit === 'hour' && !peak.diving);
	const many = $derived(peak.metrics.length > 1);
	const labels = $derived((peak.data?.rows ?? []).map((row) => row.label));

	const axis = (metric: PeakMetric) => (value: number) => (metric === 'sales' ? formatRupiahShort(value) : formatNumber(value, 0));
	const tip = (metric: PeakMetric) => (value: number) => (metric === 'sales' ? formatRupiah(value) : `${formatNumber(value, 0)}${suffix[metric]}`);
	const values = (metric: PeakMetric) => labels.map((_, index) => peak.value(metric, index));
</script>

{#if peak.data}
	<Card>
		<CardHeader
			class="mb-4"
			title={peak.diving ? format(salesPeakText.hourClockPerMinute, { hour: String(peak.data.focus_hour).padStart(2, '0') }) : format(salesPeakText.perUnit, { unit: unitLower })}
			description={peak.diving
				? peak.periodLabel
				: `${peak.periodLabel} · ${peak.repeating ? 'rata-rata tiap kemunculan' : 'jumlah per kotak'}${canDive ? ' · klik satu kolom untuk melihat per menit' : ''}`}
		>
			{#snippet actions()}
				{#if peak.diving}
					<Button label={salesPeakText.backToAllHours} icon="arrow-left" onclick={() => peak.leave()} />
				{/if}
			{/snippet}
		</CardHeader>

		<div class="flex flex-col divide-y divide-slate-100">
			{#each peak.metrics as metric (metric)}
				<div class="py-2">
					<p class="mb-1 flex items-center gap-2 text-xs font-semibold text-brand-ink">
						<span class="size-2 rounded-full" use:dynamicStyle={{ background: colors[metric] }}></span>
						{names[metric]}{peak.repeating ? ' (rata-rata)' : ''}
					</p>
					<SeriesChart
						{labels}
						series={[{ name: names[metric], values: values(metric), color: colors[metric], emphasize: true }]}
						format={axis(metric)}
						tooltipFormat={tip(metric)}
						class={many ? 'h-36 tablet:h-40' : 'h-60 tablet:h-72'}
						label={format(salesPeakText.peakChartSummary, { metric: names[metric].toLowerCase(), unit: unitLower })}
						onselect={canDive ? (index) => peak.dive(index) : undefined}
					/>
				</div>
			{/each}
		</div>

		{#if peak.repeating}
			<p class="mt-3 text-center text-xs text-slate-500">
				{format(salesPeakText.averageDrawnNote, { unit: unitLower })}
			</p>
		{/if}
	</Card>
{/if}
