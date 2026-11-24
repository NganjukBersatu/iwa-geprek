<script lang="ts">
	import { goto } from '$app/navigation';
	import { receiptBulkPath, receiptNewPath } from '$lib/nav/pages';
	import AddButton from '$lib/components/button/AddButton.svelte';
	import MoreButton from '$lib/components/button/MoreButton.svelte';
	import IngredientReceiptsView from '$lib/features/ingredient-receipts/components/ReceiptsView.svelte';
	import { IngredientReceiptsState } from '$lib/features/ingredient-receipts/ingredient-receipts.svelte';
	import { receiptColumns } from '$lib/features/ingredient-receipts/columns';
	import ManageShell from '$lib/features/manage/ManageShell.svelte';
	import { pageText } from '$lib/text/pages';

	const receipts = new IngredientReceiptsState();
</script>

<ManageShell
	manage={receipts}
	filters={receipts.filters}
	title={pageText.receiptsTitle}
	description={pageText.receiptsDescription}
	loadingText="Memuat barang masuk..."
>
	{#snippet actions()}
		<AddButton label={pageText.recordReceipt} onone={() => void goto(receiptNewPath())} onmany={() => void goto(receiptBulkPath())} />
		<MoreButton exporter={{ title: pageText.exportTitles.receipts, columns: receiptColumns, rows: () => receipts.exportRows() }} />
	{/snippet}
	{#snippet children()}
		<IngredientReceiptsView {receipts} />
	{/snippet}
</ManageShell>
