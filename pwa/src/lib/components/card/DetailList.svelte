<script lang="ts">
	import Divider from '$lib/components/feedback/Divider.svelte';
	import DetailRow from './DetailRow.svelte';
	import ListCard from './ListCard.svelte';
	import type { DetailListRow } from './types';

	/** Kartu rincian: tiap baris berisi label dan nilai teks atau konten bebas, dipisah garis. */
	let { rows }: { rows: readonly DetailListRow[] } = $props();
</script>

<ListCard>
	{#each rows as row, index (index)}
		{#if index > 0}<Divider />{/if}
		<DetailRow label={row.label} value={row.value} valueContent={row.valueContent} />
	{/each}
</ListCard>
