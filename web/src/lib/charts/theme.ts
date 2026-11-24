import { brandColors } from '$lib/charts/brand-colors';
import { formatRupiahShort } from '$lib/format/currency';

export const chartSeries = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#4a3aa7', '#e34948'] as const;

/** The brand palette in the dashboard chart: income in the primary colour, expense in the accent, profit and emphasis in the text colour. */
export const chartPalette = { income: brandColors.primary, expense: brandColors.accent, profit: brandColors.ink } as const;

/** Colours for stacked categories, in a fixed order: the palette first, then its mixes. */
export const chartCategories = [brandColors.primary, brandColors.accent, brandColors.ink, brandColors.accentDeep, brandColors.muted, brandColors.line] as const;

export const chartInk = {
	primary: '#0b0b0b',
	secondary: '#52514e',
	muted: '#898781',
	grid: '#e1e0d9',
	axis: '#c3c2b7',
	surface: '#ffffff'
} as const;

type TooltipPoint = { name?: string; axisValueLabel?: string; seriesName?: string; color?: unknown; value?: unknown };

const element = (tag: string, styles: Partial<CSSStyleDeclaration> = {}, text?: string): HTMLElement => {
	const node = document.createElement(tag);
	Object.assign(node.style, styles);
	if (text !== undefined) node.textContent = text;
	return node;
};

/** Tooltip sumbu berupa elemen DOM, bukan teks HTML: gayanya lewat objek gaya, yang CSP ketat izinkan, sedangkan atribut style tidak. */
export function axisTooltip(format: (value: number) => string) {
	return (params: TooltipPoint | TooltipPoint[]): HTMLElement => {
		const points = Array.isArray(params) ? params : [params];
		const box = element('div');
		box.append(element('div', { fontWeight: '600', marginBottom: '4px' }, points[0]?.axisValueLabel ?? points[0]?.name ?? ''));
		for (const point of points) {
			const raw = Array.isArray(point.value) ? point.value[point.value.length - 1] : point.value;
			const amount = Number(raw);
			const row = element('div', { display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '16px' });
			const label = element('span', { display: 'inline-flex', alignItems: 'center', gap: '6px' });
			label.append(element('span', { width: '8px', height: '8px', borderRadius: '9999px', backgroundColor: typeof point.color === 'string' ? point.color : chartInk.muted }), element('span', {}, point.seriesName ?? ''));
			row.append(label, element('span', { fontWeight: '600' }, Number.isFinite(amount) ? format(amount) : '-'));
			box.append(row);
		}
		return box;
	};
}

export function baseChartOptions() {
	return {
		textStyle: { fontFamily: 'Poppins, ui-sans-serif, system-ui, sans-serif' },
		grid: { left: 8, right: 16, top: 28, bottom: 8, containLabel: true },
		legend: {
			top: 0,
			left: 0,
			icon: 'roundRect',
			itemWidth: 10,
			itemHeight: 10,
			itemGap: 16,
			textStyle: { color: chartInk.secondary, fontSize: 11 }
		},
		tooltip: {
			trigger: 'axis' as const,
			axisPointer: { type: 'shadow' as const },
			backgroundColor: chartInk.surface,
			borderColor: chartInk.grid,
			borderWidth: 1,
			padding: [8, 12],
			textStyle: { color: chartInk.primary, fontSize: 12 },
			extraCssText: 'box-shadow: 0 4px 14px rgba(0,0,0,.08); border-radius: 8px;'
		},
		xAxis: {
			type: 'category' as const,
			axisLine: { lineStyle: { color: chartInk.axis } },
			axisTick: { show: false },
			axisLabel: { color: chartInk.muted, fontSize: 11 }
		},
		yAxis: {
			type: 'value' as const,
			// Whole units only, so a small figure never shows the same rounded label on two ticks.
			minInterval: 1,
			axisLine: { show: false },
			axisTick: { show: false },
			axisLabel: { color: chartInk.muted, fontSize: 11, formatter: (value: number) => formatRupiahShort(value) },
			splitLine: { lineStyle: { color: chartInk.grid, type: 'solid' as const } }
		}
	};
}

export function barSeries(name: string, data: number[], color: string) {
	return {
		name,
		type: 'bar' as const,
		data,
		barMaxWidth: 22,
		itemStyle: { color, borderRadius: [4, 4, 0, 0] }
	};
}

const heatRamp = ['#eef3fb', '#d3e1f6', '#b0c9ef', '#86ade5', '#5b8fdb', '#2a78d6', '#1f5fb1', '#17498b'];

export function heatmapOptions(max: number) {
	const base = baseChartOptions();
	return {
		grid: { left: 8, right: 16, top: 8, bottom: 8, containLabel: true },
		tooltip: { ...base.tooltip, trigger: 'item' as const, axisPointer: undefined },
		xAxis: { type: 'category' as const, data: [] as string[], axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: chartInk.muted, fontSize: 11 } },
		yAxis: {
			type: 'category' as const,
			data: [] as string[],
			inverse: true,
			axisLine: { show: false },
			axisTick: { show: false },
			axisLabel: { color: chartInk.secondary, fontSize: 11, width: 120, overflow: 'truncate' as const }
		},
		visualMap: { show: false, min: 0, max: Math.max(1, max), inRange: { color: heatRamp } }
	};
}

export function heatmapSeries(name: string, data: [number, number, number][]) {
	return {
		name,
		type: 'heatmap' as const,
		data,
		itemStyle: { borderColor: chartInk.surface, borderWidth: 2, borderRadius: 3 },
		emphasis: { itemStyle: { borderColor: chartInk.primary, borderWidth: 1 } },
		label: { show: false }
	};
}

export function dumbbellSeries(
	startName: string,
	start: number[],
	endName: string,
	end: number[],
	color: string,
	endLabel?: (index: number) => string
) {
	const base = start.map((value, index) => Math.min(value, end[index] ?? value));
	const span = start.map((value, index) => Math.abs((end[index] ?? value) - value));
	const bridge = { type: 'bar' as const, stack: 'dumbbell', barMaxWidth: 4, tooltip: { show: false }, silent: true };
	return [
		{ ...bridge, name: '_base', data: base, itemStyle: { color: 'transparent' } },
		{ ...bridge, name: '_span', data: span, itemStyle: { color: chartInk.axis, borderRadius: 2 } },
		{
			name: startName,
			type: 'scatter' as const,
			data: start.map((value, index) => [value, index]),
			symbolSize: 12,
			itemStyle: { color: chartPalette.expense, borderColor: chartInk.surface, borderWidth: 2 },
			z: 3
		},
		{
			name: endName,
			type: 'scatter' as const,
			data: end.map((value, index) => [value, index]),
			symbolSize: 12,
			itemStyle: { color, borderColor: chartInk.surface, borderWidth: 2 },
			z: 4,
			label: endLabel
				? { show: true, position: 'right' as const, distance: 8, color: chartInk.secondary, fontSize: 11, formatter: (point: { dataIndex: number }) => endLabel(point.dataIndex) }
				: { show: false }
		}
	];
}

export function peakIndex(data: number[]): number | null {
	let best = -1;
	let bestValue = 0;
	data.forEach((value, index) => {
		if (value > bestValue) {
			bestValue = value;
			best = index;
		}
	});
	return best < 0 ? null : best;
}

export function emphasisBars(name: string, data: number[], highlight: number | null, color: string, format: (value: number) => string) {
	return {
		name,
		type: 'bar' as const,
		barMaxWidth: 22,
		data: data.map((value, index) => ({
			value,
			itemStyle: { color: index === highlight ? color : chartInk.axis, borderRadius: [4, 4, 0, 0] },
			label:
				index === highlight
					? { show: true, position: 'top' as const, color: chartInk.primary, fontSize: 11, fontWeight: 600 as const, formatter: (point: { value: number }) => format(point.value) }
					: { show: false }
		}))
	};
}

export function lineSeries(name: string, data: number[], color: string) {
	return {
		name,
		type: 'line' as const,
		data,
		smooth: false,
		symbolSize: 6,
		lineStyle: { color, width: 2 },
		itemStyle: { color }
	};
}

/** A trend line without axes, labels, or hover, drawn small inside a stat card; a single value is drawn as a flat line. */
export function sparklineOptions(values: number[], color: string) {
	const data = values.length === 1 ? [values[0], values[0]] : values;
	return {
		animation: false,
		silent: true,
		grid: { left: 0, right: 0, top: 2, bottom: 2 },
		xAxis: { type: 'category' as const, show: false, boundaryGap: false, data: data.map((_, index) => index) },
		yAxis: { type: 'value' as const, show: false, scale: true },
		series: [{ type: 'line' as const, data, smooth: false, symbol: 'none', lineStyle: { color, width: 2 }, areaStyle: { color, opacity: 0.2 } }]
	};
}
