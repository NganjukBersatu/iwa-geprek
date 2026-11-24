<script lang="ts">
	import CodeBadge from '$lib/components/card/CodeBadge.svelte';
	import { SLOW_MILLIS } from '$lib/theme/ease';
	import Chart from './Chart.svelte';
	import type { DonutSlice } from './types';

	const SIZE = 160;
	const HOLE_PERCENT = '40%';
	const SLICE_SPACING = 2;
	const FONT_SIZE = 12;

	/** Donut chart with the share of each slice on it and the value legend beside it. */
	let { slices, valueText }: { slices: readonly DonutSlice[]; valueText: (value: number) => string } = $props();

	const shown = $derived(slices.filter((slice) => slice.value > 0));
	const options = $derived({
		animationDuration: SLOW_MILLIS,
		tooltip: { show: false },
		series: [
			{
				type: 'pie',
				radius: [HOLE_PERCENT, '100%'],
				silent: true,
				padAngle: shown.length > 1 ? SLICE_SPACING : 0,
				label: { show: true, position: 'inside', formatter: '{d}%', color: 'var(--color-on-primary)', fontSize: FONT_SIZE, fontWeight: 600 },
				labelLine: { show: false },
				data: shown.map((slice) => ({ name: slice.label, value: slice.value, itemStyle: { color: slice.color } }))
			}
		]
	});
	const label = $derived(shown.map((slice) => `${slice.label}: ${valueText(slice.value)}`).join(', '));
</script>

{#if shown.length > 0}
	<div class="flex items-center gap-4">
		<Chart {options} {label} height={SIZE} width={SIZE} />
		<div class="flex min-w-0 flex-col gap-2">
			{#each shown as slice (slice.label)}
				<CodeBadge text="{slice.label}: {valueText(slice.value)}" color={slice.color} />
			{/each}
		</div>
	</div>
{/if}
