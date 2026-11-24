<script lang="ts">
	import Skeleton from '../skeleton/Skeleton.svelte';
	import type { Filters } from './filters.svelte';
	import { controlText } from '$lib/text/controls';
	import { format } from '$lib/text/format';

	let { filters }: { filters: Filters } = $props();
</script>

{#if filters.active.length > 0}
	<ul class="flex flex-wrap gap-2">
		{#each filters.active as item (item.key)}
			<li class="inline-flex h-8 items-center gap-1.5 rounded-full border border-brand-tint bg-white pl-3 pr-1 text-xs">
				<span class="font-semibold text-brand-ink">{item.label}</span>
				{#if item.loading}
					<Skeleton class="h-3 w-16" />
				{:else}
					<span class="text-brand-muted">{item.text}</span>
				{/if}
				<button
					type="button"
					onclick={() => filters.clear(item.key)}
					aria-label={format(controlText.removeFilter, { name: item.label })}
					class="flex size-6 min-h-0! min-w-0! items-center justify-center rounded-full text-brand-muted transition-colors hover:bg-brand-page hover:text-brand-ink motion-reduce:transition-none"
				>
					<i class="ti ti-x text-sm" aria-hidden="true"></i>
				</button>
			</li>
		{/each}
	</ul>
{/if}
