<script lang="ts">
	import type { Snippet } from 'svelte';

	let {
		padded = true,
		flush = false,
		class: className = '',
		children
	}: {
		padded?: boolean;
		flush?: boolean;
		class?: string;
		children: Snippet;
	} = $props();
</script>

<section class="min-w-0 rounded-xl border border-brand-tint/60 bg-white {padded && !flush ? 'p-4 tablet:p-5' : ''} {flush ? 'overflow-hidden' : ''} {className}">
	{@render children()}
</section>
