<script lang="ts">
	import { goto } from '$app/navigation';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import Modal from '$lib/components/dialog/Modal.svelte';
	import BranchField from '$lib/components/form/BranchField.svelte';
	import { BRANCH_SORT, withBranchColumn } from '$lib/components/table/branch-column';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { stockItemPath } from '$lib/nav/pages';
	import { stockColumns } from '../columns';
	import { STOCK_STATUS } from '../labels';
	import type { StockItemsState } from '../stock-items.svelte';
	import { stockItemText } from '$lib/text/stock-items';

	let { stock }: { stock: StockItemsState } = $props();

	const columns = $derived(withBranchColumn(stockColumns, stock.filters.allBranches, BRANCH_SORT));

	// Which menus can be marked follows the branch chosen in the picker.
	$effect(() => {
		if (stock.picking && stock.actionBranch) void stock.loadCandidates();
	});
</script>

{#if stock.actionError && !stock.picking}
	<Banner tone="warning" icon="alert-triangle">{stock.actionError}</Banner>
{/if}

<Card flush>
	<CardHeader divided title={stockItemText.resaleItems} description={stockItemText.resaleItemsDescription} />
	{#if stock.items.length === 0}
		<Notice text={stock.query.problems ? stockItemText.noProblemItems : stockItemText.noItems} />
	{:else}
		<DataTable sort={stock.sort} {columns} rows={stock.items} rowKey={(row) => row.id} loading={stock.loading} onopen={(row) => void goto(stockItemPath(row.id))}>
			{#snippet first(row)}
				<span class="block">{row.menu_item_name}</span>
				{#if !row.is_tracked}<span class="block text-xs font-normal text-slate-500">{stockItemText.notTrackedOnSale}</span>{/if}
			{/snippet}
			{#snippet cell(row, column)}
				{#if column.key === 'status'}
					<Badge tone={STOCK_STATUS[row.status]?.tone ?? 'neutral'}>{column.value(row)}</Badge>
				{:else}
					{column.value(row)}
				{/if}
			{/snippet}
		</DataTable>
	{/if}
</Card>

{#if stock.picking}
	<Modal open title={stockItemText.manageItems} description={stockItemText.manageItemsDescription} size="md" onclose={() => stock.closeDialogs()}>
		<div class="mb-3"><BranchField bind:value={stock.actionBranch} /></div>
		{#if !stock.actionBranch}
			<Notice text={stockItemText.chooseBranchFirst} />
		{:else if stock.candidates.length === 0}
			<Notice text={stockItemText.allMenusManaged} />
		{:else}
			<ul class="flex max-h-96 flex-col divide-y divide-slate-100 overflow-y-auto">
				{#each stock.candidates as candidate (candidate.menu_item_id)}
					<li class="flex items-center justify-between gap-3 py-2">
						<span class="min-w-0">
							<span class="block truncate text-sm text-slate-800">{candidate.menu_item_name}</span>
							{#if candidate.category}<span class="block text-xs text-slate-500">{candidate.category}</span>{/if}
						</span>
						<Button label={stockItemText.mark} icon="plus" variant="tertiary" small compact disabled={stock.busy} onclick={() => void stock.mark(candidate)} />
					</li>
				{/each}
			</ul>
		{/if}
		{#if stock.actionError}<p class="mt-3 rounded-lg border border-danger-200 bg-danger-50 px-3 py-2 text-xs text-danger-700" role="alert">{stock.actionError}</p>{/if}
		{#snippet footer()}
			<Button label={stockItemText.done} variant="primary" onclick={() => stock.closeDialogs()} />
		{/snippet}
	</Modal>
{/if}
