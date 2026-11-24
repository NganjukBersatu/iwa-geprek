<script lang="ts">
	import type { Snippet } from 'svelte';
	import { reveal } from '$lib/motion/transitions';

	/** The content of a screen arriving in place of its skeleton, stacked with the page's usual gap. */
	let { children }: { children: Snippet } = $props();
</script>

<div class="flex flex-col gap-4 tablet:gap-6" in:reveal>
	{@render children()}
</div>
