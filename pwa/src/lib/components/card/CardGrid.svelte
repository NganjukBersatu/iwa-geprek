<script lang="ts" generics="T">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import type { Snippet } from 'svelte';

	const COLUMNS = 2;
	const WIDE_ROW_WEIGHT = 0.4;

	/** Kisi kartu dua kolom yang membagi tinggi tersedia rata ke semua baris; kartu sisa di baris terakhir melebar penuh dan hanya setinggi sebagian baris biasa. */
	let { items, card }: { items: readonly T[]; card: Snippet<[T]> } = $props();

	const rows = $derived(Array.from({ length: Math.ceil(items.length / COLUMNS) }, (_, index) => items.slice(index * COLUMNS, (index + 1) * COLUMNS)));
</script>

<div class="flex size-full flex-col gap-3">
	{#each rows as row, index (index)}
		<div class="flex min-h-0 w-full gap-3" use:dynamicStyle={{ flex: `${row.length === COLUMNS ? 1 : WIDE_ROW_WEIGHT} 1 0%` }}>
			{#each row as item, column (column)}
				<div class="h-full min-w-0 flex-1">{@render card(item)}</div>
			{/each}
		</div>
	{/each}
</div>
