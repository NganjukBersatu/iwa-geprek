<script lang="ts">
	import type { Snippet } from 'svelte';
	import Loadable from '$lib/components/feedback/Loadable.svelte';
	import Notice from '$lib/components/feedback/Notice.svelte';
	import ListCard from './ListCard.svelte';

	/** Kartu daftar yang menangani tiga keadaannya sendiri: memuat (kerangka), kosong (keterangan), dan berisi. */
	let {
		loading,
		empty,
		emptyText,
		skeletonRows = 3,
		children
	}: { loading: boolean; empty: boolean; emptyText: string; skeletonRows?: number; children: Snippet } = $props();
</script>

<Loadable {loading} rows={skeletonRows}>
	{#if empty}
		<ListCard><Notice text={emptyText} /></ListCard>
	{:else}
		<ListCard>{@render children()}</ListCard>
	{/if}
</Loadable>
