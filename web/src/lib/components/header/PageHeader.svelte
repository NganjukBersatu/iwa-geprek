<script lang="ts">
	import type { Snippet } from 'svelte';
	import { controlText } from '$lib/text/controls';
	import { format } from '$lib/text/format';

	let {
		title,
		description,
		leading,
		actions,
		class: className = ''
	}: {
		title: string;
		description?: string;
		leading?: Snippet;
		actions?: Snippet;
		class?: string;
	} = $props();
</script>

<svelte:head><title>{format(controlText.pageTitleWithBrand, { title: title })}</title></svelte:head>

<header class="flex flex-col gap-3 tablet:flex-row tablet:items-center tablet:justify-between {className}">
	<div class="flex min-w-0 items-center gap-3">
		{#if leading}
			{@render leading()}
		{/if}
		<div class="min-w-0">
			<h1 class="truncate text-xl font-semibold text-brand-ink">{title}</h1>
			{#if description}
				<p class="mt-0.5 max-w-3xl text-xs leading-5 text-slate-500">{description}</p>
			{/if}
		</div>
	</div>

	{#if actions}
		<div class="flex shrink-0 flex-nowrap items-center gap-2">
			{@render actions()}
		</div>
	{/if}
</header>
