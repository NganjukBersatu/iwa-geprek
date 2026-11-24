<script lang="ts">
	import BackButton from '$lib/components/button/BackButton.svelte';
	import { controlText } from '$lib/text/controls';

	/** The way back (an arrow) and the trail to the record: the last item is the page itself, an item without an address is only a label. */
	let { back, items }: { back: { label: string; href: string }; items: { label: string; href?: string }[] } = $props();
</script>

<div class="flex min-w-0 items-center gap-3">
	<BackButton label={back.label} href={back.href} />
	<nav aria-label={controlText.breadcrumb} class="min-w-0">
		<ol class="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-slate-500">
			{#each items as item, index (index)}
				{@const last = index === items.length - 1}
				<li class="flex min-w-0 items-center gap-2">
					{#if index > 0}<span aria-hidden="true">/</span>{/if}
					{#if last}
						<span aria-current="page" class="truncate font-semibold text-brand-ink">{item.label}</span>
					{:else if item.href}
						<a href={item.href} class="truncate hover:text-brand hover:underline">{item.label}</a>
					{:else}
						<span class="truncate">{item.label}</span>
					{/if}
				</li>
			{/each}
		</ol>
	</nav>
</div>
