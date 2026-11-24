<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import type { Snippet } from 'svelte';

	const WAVE_HEIGHT = 36;
	const RING_RADII = [64, 104, 144, 184];
	const RING_ALPHAS = [0.3, 0.22, 0.15, 0.09];
	const RING_STROKE = 2;
	const RING_INSET_END = 18;
	const RING_INSET_TOP = 14;
	const BUBBLE_RADII = [96, 56];
	const BUBBLE_INSET_START = 18;
	const BUBBLE_INSET_BOTTOM = 64;
	const BUBBLE_ALPHA = 0.06;
	const LARGE_DOT = { radius: 5, insetEnd: 72, insetTop: 120, alpha: 0.55 };
	const SMALL_DOT = { radius: 3, insetEnd: 48, insetTop: 150, alpha: 0.4 };
	/** Gelombang simetris dua lengkung, dirancang pada kotak 390 x 36 lalu diskalakan mengikuti lebar dan tinggi sebenarnya. */
	const WAVE_DESIGN_WIDTH = 390;
	const WAVE_DESIGN_HEIGHT = 36;

	/** Pita warna primary di puncak layar: lingkaran dekoratif dan tepi bawah bergelombang; isi berada di atasnya. */
	let { children }: { children: Snippet } = $props();

	let width = $state(390);
	let height = $state(252);

	const wave = $derived.by(() => {
		const sx = width / WAVE_DESIGN_WIDTH;
		const sy = WAVE_HEIGHT / WAVE_DESIGN_HEIGHT;
		const top = height - WAVE_HEIGHT;
		return `M0 ${height} L0 ${top + 16 * sy} C${65 * sx} ${top + 36 * sy} ${130 * sx} ${top + 36 * sy} ${195 * sx} ${top + 16 * sy} C${260 * sx} ${top + 36 * sy} ${325 * sx} ${top + 36 * sy} ${width} ${top + 16 * sy} L${width} ${height} Z`;
	});
</script>

<div class="relative flex h-full w-full flex-col items-center justify-center overflow-hidden" use:dynamicStyle={{ 'padding-bottom': `${WAVE_HEIGHT}px` }} bind:clientWidth={width} bind:clientHeight={height}>
	<svg class="pointer-events-none absolute inset-0" {width} {height} viewBox="0 0 {width} {height}" aria-hidden="true">
		<rect {width} {height} class="fill-primary" />
		{#each RING_RADII as radius, index (radius)}
			<circle cx={width - RING_INSET_END} cy={RING_INSET_TOP} r={radius} fill="none" class="stroke-accent" stroke-width={RING_STROKE} stroke-opacity={RING_ALPHAS[index]} />
		{/each}
		{#each BUBBLE_RADII as radius (radius)}
			<circle cx={BUBBLE_INSET_START} cy={height - BUBBLE_INSET_BOTTOM} r={radius} class="fill-on-primary" fill-opacity={BUBBLE_ALPHA} />
		{/each}
		<circle cx={width - LARGE_DOT.insetEnd} cy={LARGE_DOT.insetTop} r={LARGE_DOT.radius} class="fill-accent" fill-opacity={LARGE_DOT.alpha} />
		<circle cx={width - SMALL_DOT.insetEnd} cy={SMALL_DOT.insetTop} r={SMALL_DOT.radius} class="fill-accent" fill-opacity={SMALL_DOT.alpha} />
		<path d={wave} class="fill-background" />
	</svg>
	<div class="relative w-full">{@render children()}</div>
</div>
