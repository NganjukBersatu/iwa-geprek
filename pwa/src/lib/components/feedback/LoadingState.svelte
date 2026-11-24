<script lang="ts">
	import ListCard from '$lib/components/card/ListCard.svelte';
	import Divider from './Divider.svelte';
	import Skeleton from './Skeleton.svelte';
	import { t } from '$lib/text/t';

	/** Keadaan memuat berbentuk daftar: kerangka baris yang berkilau, menggantikan spinner. */
	let { rows = 4, class: className = '' }: { rows?: number; class?: string } = $props();
</script>

<div role="status" aria-live="polite" aria-label={t('common_loading')} class={className}>
	<ListCard>
		{#each { length: rows } as _, index (index)}
			{#if index > 0}<Divider />{/if}
			<div class="flex w-full items-center gap-3 p-3">
				<Skeleton class="size-[var(--space-compact)] shrink-0 !rounded-full" />
				<div class="flex flex-1 flex-col gap-2">
					<Skeleton class="h-3 w-[60%]" />
					<Skeleton class="h-3 w-[35%]" />
				</div>
			</div>
		{/each}
	</ListCard>
</div>
