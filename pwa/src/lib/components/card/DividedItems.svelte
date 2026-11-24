<script lang="ts" generics="T">
	import type { Snippet } from 'svelte';
	import Divider from '$lib/components/feedback/Divider.svelte';

	/** Menyusun [items] ke bawah dengan garis pemisah antarbaris; dipakai di dalam `ListCard`. */
	let { items, row }: { items: readonly T[]; row: Snippet<[T]> } = $props();
</script>

{#each items as item, index (index)}
	{#if index > 0}<Divider />{/if}
	{@render row(item)}
{/each}
