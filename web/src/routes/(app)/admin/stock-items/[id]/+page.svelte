<script lang="ts">
	import { page } from '$app/state';
	import StockItemDetail from '$lib/features/stock-items/components/StockItemDetail.svelte';
</script>

<StockItemDetail id={page.params['id'] as string} />
