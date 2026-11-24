<script lang="ts">
	import Button from '$lib/components/button/Button.svelte';
	import ManageShell from '$lib/features/manage/ManageShell.svelte';
	import { stockItemCountPath } from '$lib/nav/pages';
	import StockItemsView from '$lib/features/stock-items/components/StockItemsView.svelte';
	import { StockItemsState } from '$lib/features/stock-items/stock-items.svelte';
	import { pageText } from '$lib/text/pages';

	const stock = new StockItemsState();
</script>

<ManageShell
	manage={stock}
	filters={stock.filters}
	title={pageText.stockItemsTitle}
	description={pageText.stockItemsDescription}
	loadingText={pageText.loadingStockItems}
>
	{#snippet actions()}
		<Button label={pageText.manageItems} icon="list-check" compact onclick={() => void stock.openPicker()} />
		<Button label={pageText.stockCountAction} icon="clipboard-check" variant="primary" compact href={stockItemCountPath()} />
	{/snippet}
	{#snippet children()}
		<StockItemsView {stock} />
	{/snippet}
</ManageShell>
