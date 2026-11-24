<script lang="ts">
	import type { MenuItem } from '$lib/api/types';
	import Button from '$lib/components/button/Button.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import ConfirmDialog from '$lib/components/dialog/ConfirmDialog.svelte';
	import type { BranchOption } from '$lib/components/form/branch-prices.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import type { Column } from '$lib/components/table/types';
	import { formatRupiah } from '$lib/format/currency';
	import { actionText } from '$lib/text/actions';
	import { format } from '$lib/text/format';
	import { menuDetailText } from '$lib/text/menu-detail';
	import type { MenuDetailState } from '../menu-detail.svelte';
	import MenuFixedCostDialog from './MenuFixedCostDialog.svelte';

	let { menu, item }: { menu: MenuDetailState; item: MenuItem } = $props();

	const text = menuDetailText.fixedCost;
	const cost = $derived(menu.fixedCost);
	const columns = $derived<Column<BranchOption>[]>([
		{ key: 'cabang', label: text.branch, align: 'left', value: (branch) => branch.name },
		{ key: 'sumber', label: text.source, align: 'left', value: (branch) => (cost?.branch_costs[branch.id] !== undefined ? text.branchSource : text.baseSource) },
		{ key: 'biaya', label: text.cost, value: (branch) => formatRupiah(Number(cost?.branch_costs[branch.id] ?? cost?.cost ?? 0)), class: () => 'font-semibold' }
	]);
</script>

<Card flush>
	<CardHeader divided title={text.title} description={text.description}>
		{#snippet actions()}
			{#if item.has_fixed_cost}
				<Button label={actionText.edit} icon="pencil" disabled={menu.busy} onclick={() => menu.openFixedCost()} />
				<Button label={text.useRecipe} icon="receipt" disabled={menu.busy} onclick={() => menu.askClearFixedCost()} />
			{:else}
				<Button label={text.use} icon="pencil" disabled={menu.busy} onclick={() => menu.openFixedCost()} />
			{/if}
		{/snippet}
	</CardHeader>
	{#if !item.has_fixed_cost}
		<Notice text={text.notUsed} />
	{:else if menu.fixedCostError}
		<div class="p-4 tablet:p-5"><Banner tone="danger" icon="alert-triangle">{format(text.unavailable, { reason: menu.fixedCostError })}</Banner></div>
	{:else if cost}
		<DataTable {columns} rows={menu.sellers} rowKey={(branch) => branch.id} trailing="biaya" />
	{:else}
		<Notice loading text={text.loading} />
	{/if}
</Card>

{#if menu.fixedCostEditing}
	<MenuFixedCostDialog {menu} {item} />
{/if}

<ConfirmDialog
	open={menu.fixedCostClearing}
	title={format(text.clearTitle, { name: item.name })}
	confirmLabel={text.clearConfirm}
	danger
	busy={menu.busy}
	error={menu.actionError}
	onconfirm={() => void menu.confirmClearFixedCost()}
	oncancel={() => menu.closeDialogs()}
>
	{text.clearNote}
</ConfirmDialog>
