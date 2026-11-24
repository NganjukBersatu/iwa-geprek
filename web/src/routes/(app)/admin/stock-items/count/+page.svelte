<script lang="ts">
	import StockCountView from '$lib/features/stock-items/components/StockCountView.svelte';
	import { StockCountState } from '$lib/features/stock-items/stock-count.svelte';

	const count = new StockCountState();
</script>

<StockCountView {count} />
