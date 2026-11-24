<script lang="ts">
	import Badge from '$lib/components/card/Badge.svelte';
	import { formatRupiahOrDash } from '$lib/format/currency';
	import { categoryReportText } from '$lib/text/category-report';

	let { profit, complete }: { profit: string | null; complete: boolean } = $props();
</script>

{#if complete}
	{formatRupiahOrDash(profit)}
{:else}
	<span class="inline-flex flex-wrap items-center justify-end gap-1.5" title={categoryReportText.partialCostHint}>
		{formatRupiahOrDash(profit)}
		{#if profit !== null}<Badge tone="warning" title={categoryReportText.partialCostHint}>{categoryReportText.partialCost}</Badge>{/if}
	</span>
{/if}
