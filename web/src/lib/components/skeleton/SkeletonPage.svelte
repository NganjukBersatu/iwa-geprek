<script lang="ts">
	import Card from '../card/Card.svelte';
	import Skeleton from './Skeleton.svelte';
	import SkeletonList from './SkeletonList.svelte';
	import { controlText } from '$lib/text/controls';

	let {
		stats = 4,
		label = controlText.pageLoading
	}: {
		/** Placeholder tiles in the row above; 0 for pages that open straight on a list. */
		stats?: number;
		label?: string;
	} = $props();
</script>

<div class="flex flex-col gap-4 tablet:gap-6" role="status" aria-label={label} aria-busy="true">
	{#if stats > 0}
		<div class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-4">
			{#each { length: stats } as _, tile (tile)}
				<div class="flex flex-col gap-3 rounded-xl border border-slate-100 bg-white p-4">
					<Skeleton class="h-3 w-1/3" />
					<Skeleton class="h-7 w-2/3" />
					<Skeleton class="h-3 w-1/2" />
				</div>
			{/each}
		</div>
	{/if}
	<Card flush>
		<div class="border-b border-slate-100 px-4 py-4 tablet:px-5"><Skeleton class="h-4 w-48" /></div>
		<SkeletonList rows={5} {label} />
	</Card>
</div>
