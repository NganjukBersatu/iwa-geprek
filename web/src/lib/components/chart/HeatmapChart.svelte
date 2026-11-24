<script lang="ts">
	import { dynamicStyle } from '$lib/motion/actions';
	import { heatmapOptions, heatmapSeries } from '$lib/charts/theme';
	import { formatNumber } from '$lib/format/currency';
	import Chart from './Chart.svelte';

	let {
		columns,
		rows,
		unit = 'item',
		label
	}: {
		columns: string[];
		rows: { label: string; values: number[] }[];
		unit?: string;
		label: string;
	} = $props();

	const minWidth = $derived(150 + columns.length * 30);
	const height = $derived(Math.max(140, rows.length * 30 + 44));

	const options = $derived.by(() => {
		const cells: [number, number, number][] = [];
		let max = 0;
		rows.forEach((row, y) => {
			row.values.forEach((value, x) => {
				cells.push([x, y, value]);
				if (value > max) max = value;
			});
		});
		const base = heatmapOptions(max);
		return {
			...base,
			xAxis: { ...base.xAxis, data: columns },
			yAxis: { ...base.yAxis, data: rows.map((row) => row.label) },
			series: [heatmapSeries(unit, cells)],
			tooltip: {
				...base.tooltip,
				formatter: (point: { value: [number, number, number] }) => {
					const [x, y, value] = point.value;
					return `<b>${rows[y]?.label ?? ''}</b><br/>${columns[x] ?? ''}: <b>${formatNumber(value, 0)}</b> ${unit}`;
				}
			}
		};
	});
</script>

<div class="overflow-x-auto">
	<div use:dynamicStyle={{ 'min-width': `${minWidth}px` }}>
		<Chart {options} {height} {label} />
	</div>
</div>
