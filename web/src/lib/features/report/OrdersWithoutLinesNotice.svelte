<script lang="ts">
	import Banner from '$lib/components/card/Banner.svelte';
	import { formatNumber, formatRupiah } from '$lib/format/currency';
	import { format } from '$lib/text/format';
	import { pageText } from '$lib/text/pages';

	let { count, revenue }: { count: number; revenue: string } = $props();
</script>

{#if count > 0}
	<Banner tone="warning" icon="alert-triangle" title={format(pageText.ordersWithoutLinesTitle, { count: formatNumber(count, 0) })}>
		{format(pageText.ordersWithoutLinesBody, { revenue: formatRupiah(revenue) })}
	</Banner>
{/if}
