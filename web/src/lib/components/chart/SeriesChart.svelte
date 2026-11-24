<script lang="ts">
	import { axisTooltip, baseChartOptions, barSeries, chartInk, emphasisBars, lineSeries, peakIndex } from '$lib/charts/theme';
	import { formatRupiahShort } from '$lib/format/currency';
	import Chart from './Chart.svelte';

	type Series = {
		name: string;
		values: number[];
		color: string;
		kind?: 'bar' | 'line';
		emphasize?: boolean;
		stack?: string;
	};

	let {
		labels,
		series,
		format = formatRupiahShort,
		tooltipFormat = format,
		legend = series.length > 1,
		label,
		class: className = 'h-60 tablet:h-72',
		height,
		onselect
	}: {
		labels: string[];
		series: Series[];
		format?: (value: number) => string;
		tooltipFormat?: (value: number) => string;
		legend?: boolean;
		label: string;
		class?: string;
		height?: number;
		onselect?: (index: number) => void;
	} = $props();

	const empty = $derived(series.every((item) => item.values.every((value) => value === 0)));

	const options = $derived.by(() => {
		const base = baseChartOptions();
		return {
			...base,
			legend: { ...base.legend, show: legend },
			grid: { ...base.grid, top: legend ? 28 : 24 },
			xAxis: { ...base.xAxis, data: labels, axisLabel: { ...base.xAxis.axisLabel, interval: labels.length > 40 ? 'auto' : 0, hideOverlap: true } },
			yAxis: { ...base.yAxis, axisLabel: { color: chartInk.muted, fontSize: 11, formatter: format }, splitNumber: 3 },
			series: series.map((item) =>
				item.kind === 'line'
					? lineSeries(item.name, item.values, item.color)
					: item.emphasize
						? emphasisBars(item.name, item.values, peakIndex(item.values), item.color, format)
						: { ...barSeries(item.name, item.values, item.color), stack: item.stack }
			),
			tooltip: { ...base.tooltip, formatter: axisTooltip(tooltipFormat) }
		};
	});
</script>

<Chart {options} {label} {height} {empty} class={className} {onselect} />
