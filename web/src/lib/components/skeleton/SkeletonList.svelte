<script lang="ts">
	import Skeleton from './Skeleton.svelte';
	import { controlText } from '$lib/text/controls';

	let {
		rows = 4,
		avatar = false,
		label = controlText.loading
	}: {
		rows?: number;
		/** A round tile at the start of each row, for lists of people. */
		avatar?: boolean;
		label?: string;
	} = $props();

	const WIDTHS = ['w-2/3', 'w-1/2', 'w-3/4', 'w-3/5'];
</script>

<ul class="divide-y divide-slate-100" role="status" aria-label={label} aria-busy="true">
	{#each { length: rows } as _, line (line)}
		<li class="flex items-center gap-3 px-4 py-4 tablet:gap-4 tablet:px-5">
			{#if avatar}<Skeleton class="size-10 shrink-0 rounded-lg" />{/if}
			<span class="flex min-w-0 flex-1 flex-col gap-2">
				<Skeleton class="h-4 {WIDTHS[line % WIDTHS.length]}" />
				<Skeleton class="h-3 w-1/3" />
			</span>
			<Skeleton class="h-4 w-16 shrink-0" />
		</li>
	{/each}
</ul>
