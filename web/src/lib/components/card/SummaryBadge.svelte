<script lang="ts">
	import type { Snippet } from 'svelte';
	import { summaryAccents, type SummaryAccent } from './summary-accent';

	let {
		accent,
		title,
		label,
		children
	}: {
		accent: SummaryAccent;
		title?: string | undefined;
		label?: string | undefined;
		children: Snippet;
	} = $props();
</script>

<span
	{title}
	aria-label={label}
	class="inline-flex h-5 items-center gap-1 whitespace-nowrap rounded-full px-2 text-xs font-semibold {summaryAccents[accent].solid}"
>
	{@render children()}
</span>
