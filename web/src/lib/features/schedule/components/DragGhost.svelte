<script lang="ts">
	import { dynamicStyle } from '$lib/motion/actions';
	import type { Drag } from '../drag.svelte';

	let { drag }: { drag: Drag } = $props();
</script>

{#if drag.item}
	<div class="pointer-events-none fixed z-60 -translate-x-1/2 -translate-y-1/2 rounded-lg border border-brand bg-white px-3 py-1.5 text-xs font-semibold text-brand shadow-xl" use:dynamicStyle={{ left: `${drag.x}px`, top: `${drag.y}px` }}>
		{drag.item.label}
	</div>
{/if}
