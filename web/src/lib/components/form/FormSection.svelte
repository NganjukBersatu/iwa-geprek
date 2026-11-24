<script lang="ts">
	import type { Snippet } from 'svelte';
	import Card from '$lib/components/card/Card.svelte';

	/**
	 * One group of related fields. Without an icon its title sits beside the fields on a wide screen; with an icon it is a card of its own,
	 * the icon tile, title and explanation on top and the fields below, for a page whose groups are stacked (FormPage stacked).
	 */
	let { title, description, icon, children }: { title: string; description?: string; icon?: string; children: Snippet } = $props();
</script>

{#if icon}
	<Card class="flex flex-col gap-3">
		<div class="flex items-center gap-3">
			<span class="flex size-8 shrink-0 items-center justify-center rounded-md border border-slate-100 bg-brand-soft text-brand"><i class="ti ti-{icon} text-base" aria-hidden="true"></i></span>
			<div class="min-w-0">
				<h2 class="text-sm font-semibold text-brand-ink">{title}</h2>
				{#if description}<p class="text-xs leading-4 text-slate-500">{description}</p>{/if}
			</div>
		</div>
		<div class="flex min-w-0 flex-col gap-2">{@render children()}</div>
	</Card>
{:else}
	<section class="grid gap-3 py-5 first:pt-0 last:pb-0 laptop:grid-cols-[minmax(0,16rem)_minmax(0,1fr)] laptop:gap-8">
		<div>
			<h2 class="text-base font-semibold text-brand-ink">{title}</h2>
			{#if description}
				<p class="mt-1 text-xs leading-5 text-slate-500">{description}</p>
			{/if}
		</div>
		<div class="flex min-w-0 flex-col gap-4">{@render children()}</div>
	</section>
{/if}
