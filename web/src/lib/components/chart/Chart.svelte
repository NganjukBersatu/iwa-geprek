<script lang="ts">
	import { dynamicStyle } from '$lib/motion/actions';
	import { onMount } from 'svelte';
	import { chartText } from '$lib/text/chart';
	import Notice from '../card/Notice.svelte';

	type EChart = {
		setOption: (option: unknown, notMerge?: boolean) => void;
		resize: () => void;
		dispose: () => void;
		on: (event: string, handler: (point: unknown) => void) => void;
	};

	let {
		options,
		label,
		class: className = 'h-64',
		height,
		empty = false,
		onselect
	}: {
		options: Record<string, unknown>;
		label: string;
		class?: string;
		height?: number;
		/** True when there is nothing to draw: the chart is replaced by an explanation, and comes back when data arrives. */
		empty?: boolean;
		onselect?: (index: number) => void;
	} = $props();

	let container: HTMLDivElement;
	let chart: EChart | null = null;

	onMount(() => {
		let cancelled = false;
		let observer: ResizeObserver | null = null;

		void (async () => {
			const { createChart } = await import('$lib/charts/chart-engine');
			if (cancelled || !container) return;
			const instance: EChart = createChart(container);
			chart = instance;
			instance.setOption(options);
			instance.on('click', (point) => onselect?.((point as { dataIndex: number }).dataIndex));
			observer = new ResizeObserver(() => instance.resize());
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
		const next = options;
		if (chart) chart.setOption(next, true);
	});
</script>

{#if empty}
	<div use:dynamicStyle={{ height: height ? `${height}px` : undefined }} class="flex w-full items-center rounded-lg border border-slate-100 bg-slate-50 {height ? '' : className}">
		<Notice title={chartText.empty.title} text={chartText.empty.text} />
	</div>
{/if}
<div bind:this={container} role="img" aria-label={label} use:dynamicStyle={{ display: empty ? 'none' : undefined, height: height ? `${height}px` : undefined }} class="w-full {height ? '' : className}"></div>
