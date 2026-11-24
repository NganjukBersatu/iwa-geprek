<script lang="ts" generics="T">
	import type { Snippet } from 'svelte';
	import DividedItems from '$lib/components/card/DividedItems.svelte';
	import StateListCard from '$lib/components/card/StateListCard.svelte';
	import Divider from '$lib/components/feedback/Divider.svelte';
	import Pagination from './Pagination.svelte';

	/** Kartu daftar berhalaman: [items] adalah isi halaman yang sedang tampil; kerangka, keadaan kosong, garis pemisah, dan pengatur halaman (hanya bila [pageCount] > 1) ditangani di sini. */
	let {
		items,
		page,
		pageCount,
		onPageChange,
		emptyText,
		loading = false,
		skeletonRows = 3,
		row
	}: { items: readonly T[]; page: number; pageCount: number; onPageChange: (page: number) => void; emptyText: string; loading?: boolean; skeletonRows?: number; row: Snippet<[T]> } = $props();
</script>

<StateListCard {loading} empty={items.length === 0} {emptyText} {skeletonRows}>
	<DividedItems {items} {row} />
	{#if pageCount > 1}
		<Divider />
		<Pagination page={Math.min(Math.max(page, 0), pageCount - 1)} {pageCount} {onPageChange} />
	{/if}
</StateListCard>
