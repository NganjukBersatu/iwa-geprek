<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import { goto } from '$app/navigation';
	import Button from '$lib/components/button/Button.svelte';
	import BranchPriceBadge from '$lib/components/form/BranchPriceBadge.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import ListSearch from '$lib/components/filter/ListSearch.svelte';
	import { noMatchText } from '$lib/components/filter/no-match';
	import Notice from '$lib/components/card/Notice.svelte';
	import type { Field } from '$lib/components/form/types';
	import Pager from '$lib/components/pager/Pager.svelte';
	import BulkActions from '$lib/components/table/BulkActions.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import type { MenuState } from '../menu.svelte';
	import { menuColumns } from '../columns';
	import { menuNewPath, menuPath } from '$lib/nav/pages';
	import MenuForm from './MenuForm.svelte';
	import { termText } from '$lib/text/terms';
	import { menuText } from '$lib/text/menu';
	import { format } from '$lib/text/format';

	let { menu }: { menu: MenuState } = $props();

	const columns = $derived(menuColumns(menu.outlets));

	const changeFields = $derived<Field[]>([
		{ key: 'category_id', label: termText.category, kind: 'select', options: menu.categories.map((category) => ({ value: category.id, label: category.name })) },
		{ key: 'is_available', label: menuText.availability, kind: 'toggle', yes: menuText.available, no: termText.outOfStock }
	]);
</script>

{#if menu.actionError && !menu.changeOpen && !menu.bulkRemoveOpen}
	<Banner tone="danger" icon="alert-triangle">{menu.actionError}</Banner>
{/if}

<Card flush>
	<CardHeader divided title={menuText.listTitle} description={menuText.listDescription} />
	<ListSearch value={menu.search} placeholder={menuText.searchPlaceholder} label={controlText.searchMenu} onsearch={(query) => menu.setSearch(query)} />
	{#if menu.items.length === 0}
		{@const noMatch = noMatchText('menu', menu.search !== '', menu.filters.count > 0)}
		{#if noMatch}
			<Notice text={noMatch} />
		{:else}
			<Notice title={menuText.noMenus} text={menuText.noMenusHint}/>
		{/if}
	{:else}
		<DataTable {columns} rows={menu.items} rowKey={(row) => row.id} loading={menu.loading} selection={menu.selection} sort={menu.sort} trailing="harga" onopen={(row) => void goto(menuPath(row.id))}>
			{#snippet first(row)}
				<span class="inline-flex items-center gap-2">
					{#if row.image_url}<img src={row.image_url} alt="" class="size-8 rounded-lg object-cover" />{/if}
					<span>{row.name}</span>
					{#if !row.is_available}<Badge tone="danger">{menuText.offEverywhere}</Badge>{:else if row.unavailable_outlet_ids.length > 0}<Badge tone="danger">{format(menuText.outOfStockAtBranches, { count: row.unavailable_outlet_ids.length })}</Badge>{/if}
					<BranchPriceBadge item={row} />
				</span>
			{/snippet}
		</DataTable>
		<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
			<Pager page={menu.page} total={menu.total} unit="menu" disabled={menu.loading} onchange={(page) => menu.setPage(page)} />
		</div>
	{/if}
</Card>

<BulkActions
	selection={menu.selection}
	noun="menu"
	bind:removing={menu.bulkRemoveOpen}
	bind:changing={menu.changeOpen}
	fields={changeFields}
	onchange={(changes) => void menu.changeSelected(changes)}
	busy={menu.busy}
	error={menu.actionError}
	onremove={() => void menu.removeSelected()}
	oncancel={() => menu.closeDialogs()}
>
	{menuText.bulkRemoveNote}
</BulkActions>
