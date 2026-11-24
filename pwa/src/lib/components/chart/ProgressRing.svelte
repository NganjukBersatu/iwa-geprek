<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import { textColor, type ColorToken } from '$lib/theme/colors';
	import { SLOW_MILLIS } from '$lib/theme/ease';
	import Chart from './Chart.svelte';

	const FILL_DURATION_FACTOR = 2;
	const STROKE = 8;

	/** Progress ring with its label in the middle; it fills gradually whenever the value changes. */
	let {
		progress,
		label,
		trackColor,
		indicatorColor,
		labelColor,
		size = 64
	}: { progress: number; label: string; trackColor: ColorToken; indicatorColor: ColorToken; labelColor: ColorToken; size?: number } = $props();

	const options = $derived({
		animationDuration: SLOW_MILLIS * FILL_DURATION_FACTOR,
		animationDurationUpdate: SLOW_MILLIS * FILL_DURATION_FACTOR,
		series: [
			{
				type: 'gauge',
				startAngle: 90,
				endAngle: -270,
				min: 0,
				max: 1,
				radius: '100%',
				silent: true,
				pointer: { show: false },
				progress: { show: true, roundCap: true, width: STROKE, itemStyle: { color: `var(--color-${indicatorColor})` } },
				axisLine: { lineStyle: { width: STROKE, color: [[1, `var(--color-${trackColor})`]] } },
				axisTick: { show: false },
				splitLine: { show: false },
				axisLabel: { show: false },
				detail: { show: false },
				data: [{ value: Math.min(1, Math.max(0, progress)) }]
			}
		]
	});
</script>

<div class="relative shrink-0" use:dynamicStyle={{ width: `${size}px`, height: `${size}px` }}>
	<Chart {options} {label} height={size} width={size} />
	<span class="text-label absolute inset-0 flex items-center justify-center {textColor[labelColor]}" aria-hidden="true">{label}</span>
</div>
