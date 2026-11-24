<script lang="ts">
	import type { Snippet } from 'svelte';

	let {
		text,
		title,
		loading = false,
		class: className = '',
		children
	}: {
		text: string;
		/** A short heading for an empty state; it names what is missing, the text says what to do next. */
		title?: string;
		loading?: boolean;
		class?: string;
		/** The one action that leads out of an empty state, such as a button that adds the first item. */
		children?: Snippet;
	} = $props();
</script>

{#if loading}
	<p class="flex items-center justify-center gap-2 py-6 text-center text-sm text-slate-600 {className}">
		<i class="ti ti-loader-2 animate-spin" aria-hidden="true"></i>
		{text}
	</p>
{:else}
	<div class="flex flex-col items-start gap-1 px-4 py-6 tablet:px-5 {className}">
		{#if title}<p class="text-base font-semibold text-slate-800">{title}</p>{/if}
		<p class="max-w-prose text-sm text-slate-600">{text}</p>
		{#if children}<div class="mt-3">{@render children()}</div>{/if}
	</div>
{/if}
