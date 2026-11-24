<script lang="ts">
	import type { Snippet } from 'svelte';
	import { controlText } from '$lib/text/controls';
	import { format } from '$lib/text/format';

	/** The top of a page that has a trail: the trail to this page, then its title and one line of explanation, plain on the page, with the actions beside the title. */
	let {
		title,
		description,
		items,
		badge,
		actions
	}: {
		title: string;
		description?: string;
		items: { label: string; href?: string }[];
		/** A status shown beside the title. */
		badge?: Snippet;
		actions?: Snippet;
	} = $props();
</script>

<svelte:head><title>{format(controlText.pageTitleWithBrand, { title: title })}</title></svelte:head>

<header class="flex flex-col gap-4">
	<nav aria-label={controlText.breadcrumb}>
		<ol class="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs">
			{#each items as item, index (index)}
				{@const last = index === items.length - 1}
				<li class="flex min-w-0 items-center gap-2">
					{#if index > 0}<i class="ti ti-chevron-right text-slate-400" aria-hidden="true"></i>{/if}
					{#if last}
						<span aria-current="page" class="truncate font-semibold text-brand-ink">{item.label}</span>
					{:else if item.href}
						<a href={item.href} class="truncate font-semibold text-slate-500 hover:text-brand hover:underline">{item.label}</a>
					{:else}
						<span class="truncate font-semibold text-slate-500">{item.label}</span>
					{/if}
				</li>
			{/each}
		</ol>
	</nav>
	<div class="flex flex-col gap-3 tablet:flex-row tablet:items-start tablet:justify-between">
		<div class="min-w-0">
			<div class="flex flex-wrap items-center gap-3">
				<h1 class="text-xl font-semibold text-brand-ink">{title}</h1>
				{#if badge}{@render badge()}{/if}
			</div>
			{#if description}
				<p class="mt-0.5 max-w-3xl text-xs leading-5 text-slate-500">{description}</p>
			{/if}
		</div>
		{#if actions}
			<div class="flex shrink-0 flex-wrap items-center gap-2">{@render actions()}</div>
		{/if}
	</div>
</header>
