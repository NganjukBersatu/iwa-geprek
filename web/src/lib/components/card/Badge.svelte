<script lang="ts">
	import type { Snippet } from 'svelte';
	import { tones, type Tone } from './tone';

	let {
		tone = 'neutral',
		title,
		children
	}: {
		tone?: Tone;
		title?: string;
		children: Snippet;
	} = $props();
</script>

<span {title} class="inline-flex items-center gap-1 whitespace-nowrap rounded-full border px-2 py-0.5 text-xs font-semibold {tones[tone].pill}">
	{@render children()}
</span>
