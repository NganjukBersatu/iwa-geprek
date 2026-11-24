<script lang="ts">
	import { baseChartOptions, chartInk, chartPalette, dumbbellSeries } from '$lib/charts/theme';
	import { formatRupiahShort } from '$lib/format/currency';
	import Chart from './Chart.svelte';

	type Row = { label: string; from: number; to: number; note?: string; detail: string };

	let {
		rows,
		fromName,
		toName,
		format = formatRupiahShort,
		label
	}: {
		rows: Row[];
		fromName: string;
		toName: string;
		format?: (value: number) => string;
		label: string;
	} = $props();

	const height = $derived(Math.max(220, rows.length * 34 + 60));

	const options = $derived.by(() => {
		const base = baseChartOptions();
		return {
			...base,
			grid: { ...base.grid, right: 64 },
			legend: { ...base.legend, data: [fromName, toName] },
			xAxis: {
				type: 'value' as const,
				axisLine: { show: false },
				axisTick: { show: false },
				axisLabel: { color: chartInk.muted, fontSize: 11, formatter: format },
				splitLine: base.yAxis.splitLine
			},
			yAxis: {
				type: 'category' as const,
				inverse: true,
				data: rows.map((row) => row.label),
				axisLine: { show: false },
				axisTick: { show: false },
				axisLabel: { color: chartInk.secondary, fontSize: 11, width: 120, overflow: 'truncate' as const }
			},
			series: dumbbellSeries(fromName, rows.map((row) => row.from), toName, rows.map((row) => row.to), chartPalette.income, (index) => rows[index]?.note ?? ''),
			tooltip: {
				...base.tooltip,
				trigger: 'item' as const,
				axisPointer: undefined,
				formatter: (point: { value: [number, number] }) => {
					const row = rows[point.value[1]];
					return row ? `<b>${row.label}</b><br/>${row.detail}` : '';
				}
			}
		};
	});
</script>

<Chart {options} {height} {label} />
