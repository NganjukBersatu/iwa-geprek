<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import { onMount } from 'svelte';

	type EChart = {
		setOption: (option: unknown, notMerge?: boolean) => void;
		resize: () => void;
		dispose: () => void;
	};

	/** The single echarts surface of the PWA; colors may be written as theme tokens "var(--color-...)" and are read from app.css. */
	let {
		options,
		label,
		height,
		width
	}: {
		options: Record<string, unknown>;
		label: string;
		height: number;
		width?: number;
	} = $props();

	let container: HTMLDivElement;
	let chart: EChart | null = null;

	const TOKEN = /^var\((--[\w-]+)\)$/;
	const SPACED_RGB = /^rgba?\(\s*(\d+)\s+(\d+)\s+(\d+)\s*(?:\/\s*([\d.]+%?))?\s*\)$/;

	// The canvas renderer reads plain colors only, so theme tokens become their computed value and space-separated rgb becomes rgba.
	function resolve(value: unknown, styles: CSSStyleDeclaration): unknown {
		if (typeof value === 'string') {
			const name = TOKEN.exec(value)?.[1];
			const color = name ? styles.getPropertyValue(name).trim() : value;
			const rgb = SPACED_RGB.exec(color);
			if (!rgb) return color;
			const alpha = rgb[4] === undefined ? 1 : rgb[4].endsWith('%') ? parseFloat(rgb[4]) / 100 : parseFloat(rgb[4]);
			return `rgba(${rgb[1]}, ${rgb[2]}, ${rgb[3]}, ${alpha})`;
		}
		if (Array.isArray(value)) return value.map((item) => resolve(item, styles));
		if (value && typeof value === 'object' && Object.getPrototypeOf(value) === Object.prototype) {
			return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, resolve(item, styles)]));
		}
		return value;
	}

	function render(next: Record<string, unknown>) {
		if (chart && container) chart.setOption(resolve(next, getComputedStyle(container)), true);
	}

	onMount(() => {
		let cancelled = false;
		let observer: ResizeObserver | null = null;

		void (async () => {
			const [core, charts, components, renderers] = await Promise.all([
				import('echarts/core'),
				import('echarts/charts'),
				import('echarts/components'),
				import('echarts/renderers')
			]);
			if (cancelled || !container) return;
			core.use([charts.BarChart, charts.PieChart, charts.GaugeChart, components.GridComponent, components.TooltipComponent, renderers.CanvasRenderer]);
			chart = core.init(container, undefined, { renderer: 'canvas' });
			render(options);
			observer = new ResizeObserver(() => chart?.resize());
			observer.observe(container);
		})();

		return () => {
			cancelled = true;
			observer?.disconnect();
			chart?.dispose();
			chart = null;
		};
	});

	$effect(() => {
		render(options);
	});
</script>

<div bind:this={container} role="img" aria-label={label} class="shrink-0" use:dynamicStyle={{ height: `${height}px`, width: width ? `${width}px` : '100%' }}></div>
