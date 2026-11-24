<script lang="ts">
	import Badge from '../card/Badge.svelte';
	import { branchPriceCount, type BranchPriced } from './branch-prices.svelte';
	import { controlText } from '$lib/text/controls';
	import { format } from '$lib/text/format';

	let { item }: { item: BranchPriced } = $props();

	const count = $derived(branchPriceCount(item));
</script>

{#if count > 0}<Badge tone="info">{format(controlText.branchPricesCount, { count: count })}</Badge>{/if}
