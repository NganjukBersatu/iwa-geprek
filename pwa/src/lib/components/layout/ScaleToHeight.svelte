<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import type { Snippet } from 'svelte';

	const MIN_SCALE = 0.7;
	const MAX_SCALE = 1.5;

	/** Memperbesar atau memperkecil isi (teks, ikon, jarak) mengikuti tinggi yang diberikan; [baseline] adalah tinggi alaminya, [baselineWidth] lebar alami yang membatasi skala agar isi tidak terpotong. */
	let { baseline, baselineWidth, children }: { baseline: number; baselineWidth?: number; children: Snippet } = $props();

	let width = $state(0);
	let height = $state(0);

	const scale = $derived.by(() => {
		if (height === 0) return 1;
		const byHeight = height / baseline;
		const byWidth = baselineWidth ? width / baselineWidth : Number.POSITIVE_INFINITY;
		return Math.min(MAX_SCALE, Math.max(MIN_SCALE, Math.min(byHeight, byWidth)));
	});
</script>

<div class="h-full w-full overflow-hidden" bind:clientWidth={width} bind:clientHeight={height}>
	<div class="h-full w-full" use:dynamicStyle={{ zoom: scale }}>{@render children()}</div>
</div>
