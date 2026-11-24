<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import type { BarSegment } from './types';

	/** Bagian terkecil yang tetap bisa disentuh, sebagai porsi lebar seluruh bilah. */
	const MIN_SHARE = 0.14;

	/** Bilah berbagian yang lebarnya sebanding bobot, tanpa bingkai; setiap bagian bisa diketuk. */
	let { segments, onselect }: { segments: readonly BarSegment[]; onselect: (index: number) => void } = $props();

	const total = $derived(Math.max(1, segments.reduce((sum, segment) => sum + segment.weight, 0)));
</script>

<div class="flex h-12 w-full gap-2">
	{#each segments as segment, index (index)}
		<button
			type="button"
			aria-label={String(index + 1)}
			onclick={() => onselect(index)}
			class="relative h-full overflow-hidden rounded-field bg-selected"
			use:dynamicStyle={{ flex: `${Math.max(segment.weight, total * MIN_SHARE)} 1 0%` }}
		>
			<span
				class="absolute inset-y-0 left-0 block {segment.tone === 'primary' ? 'bg-primary' : 'bg-accent'}"
				use:dynamicStyle={{ width: `${Math.min(1, Math.max(0, segment.progress)) * 100}%`, transition: 'width var(--effect-standard) var(--ease-standard)' }}
			></span>
		</button>
	{/each}
</div>
