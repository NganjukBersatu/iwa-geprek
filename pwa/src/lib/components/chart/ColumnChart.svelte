<script lang="ts">
	import { axisTooltip } from './axis-tooltip';
	import { SLOW_MILLIS } from '$lib/theme/ease';
	import Chart from './Chart.svelte';

	const CHART_HEIGHT = 200;
	const COLUMN_THICKNESS = 20;
	const MAX_TICKS = 4;
	const FONT_SIZE = 12;

	/** Column chart: one column per value, [labels] on the bottom axis and [axisText] on the left axis. */
	let { values, labels, axisText }: { values: readonly number[]; labels: readonly string[]; axisText: (value: number) => string } = $props();

	const options = $derived({
		animationDuration: SLOW_MILLIS,
		grid: { left: 8, right: 8, top: 12, bottom: 4, containLabel: true },
		tooltip: {
			trigger: 'axis',
			axisPointer: { type: 'shadow' },
			backgroundColor: 'var(--color-surface)',
			borderColor: 'var(--color-divider)',
			textStyle: { color: 'var(--color-content)', fontSize: FONT_SIZE },
			formatter: axisTooltip(axisText)
		},
		xAxis: {
			type: 'category',
			data: [...labels],
			axisLine: { lineStyle: { color: 'var(--color-divider)' } },
			axisTick: { show: false },
			axisLabel: { color: 'var(--color-content)', fontSize: FONT_SIZE, interval: 0, hideOverlap: true }
		},
		yAxis: {
			type: 'value',
			minInterval: 1,
			splitNumber: MAX_TICKS,
			axisLabel: { color: 'var(--color-content)', fontSize: FONT_SIZE, formatter: (value: number) => axisText(value) },
			splitLine: { lineStyle: { color: 'var(--color-divider)' } }
		},
		series: [{ type: 'bar', data: [...values], barMaxWidth: COLUMN_THICKNESS, itemStyle: { color: 'var(--color-primary)' } }]
	});
	const label = $derived(labels.map((name, index) => `${name}: ${axisText(values[index] ?? 0)}`).join(', '));
</script>

{#if values.length > 0}
	<Chart {options} {label} height={CHART_HEIGHT} />
{/if}
