<script lang="ts">
	import { goto } from '$app/navigation';
	import { ingredientNewPath, ingredientPath } from '$lib/nav/pages';
	import { emptyText } from '$lib/text/empty';
	import Button from '$lib/components/button/Button.svelte';
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
	import { formatNumber } from '$lib/format/currency';
	import type { IngredientsState } from '../ingredients.svelte';
	import { ingredientColumns } from '../columns';
	import { stockBadge } from '../stock-level';
	import CatalogDialog from './CatalogDialog.svelte';
	import { termText } from '$lib/text/terms';
	import { ingredientText } from '$lib/text/ingredients';
	import { format } from '$lib/text/format';

	let { ingredients }: { ingredients: IngredientsState } = $props();

	const columns = ingredientColumns;

	const categoryOptions = $derived(ingredients.options.categories.map((item) => ({ value: item.id, label: item.name })));

	const changeFields = $derived<Field[]>([
		{ key: 'category_id', label: termText.category, kind: 'select', options: categoryOptions },
		{ key: 'minimum', label: ingredientText.minimumLimit, kind: 'number' },
		{ key: 'shrink_tolerance', label: ingredientText.shrinkTolerancePercent, kind: 'number' },
		{ key: 'is_active', label: termText.status, kind: 'toggle', yes: termText.active, no: termText.inactive }
	]);
</script>

{#if ingredients.actionError}
	<Banner tone="warning" icon="alert-triangle">{ingredients.actionError}</Banner>
{/if}
{#if ingredients.unlinked > 0}
	<Banner tone="warning" icon="link-off" title={ingredientText.unlinkedTitle}>{format(ingredientText.ingredientsUnlinked, { count: formatNumber(ingredients.unlinked, 0) })}</Banner>
{/if}

<Card flush>
	<CardHeader divided title={ingredientText.listTitle} description={format(ingredientText.ingredientsCaption, { count: formatNumber(ingredients.total, 0) })} />
	<ListSearch value={ingredients.search} placeholder={ingredientText.searchPlaceholder} label={ingredientText.search} onsearch={(query) => ingredients.setSearch(query)} />
	{#if ingredients.items.length === 0}
		{@const noMatch = noMatchText('bahan', ingredients.search !== '', ingredients.filters.count > 0)}
		{#if noMatch}
			<Notice text={noMatch} />
		{:else}
			<Notice title={emptyText.ingredients.title} text={emptyText.ingredients.text}/>
		{/if}
	{:else}
		<DataTable sort={ingredients.sort} {columns} rows={ingredients.items} rowKey={(row) => row.id} loading={ingredients.loading} selection={ingredients.selection} onopen={(row) => void goto(ingredientPath(row.id))}>
			{#snippet first(row)}
				<span class="flex items-center gap-3">
					{#if row.photo_url}
						<img src={row.photo_url} alt="" class="size-9 shrink-0 rounded-lg border border-slate-200 object-cover" />
					{/if}
					<span class="min-w-0">
						<span class="block">{row.name}</span>
						<span class="block text-xs font-normal text-slate-500">{ingredients.branchName(row.outlet_id)}{row.branch_count > 1 ? ` · dipakai ${row.branch_count} cabang` : ''}</span>
					</span>
				</span>
			{/snippet}
			{#snippet cell(row, column)}
				{#if column.key === 'saldo'}
					<span class="inline-flex flex-wrap items-center justify-end gap-1.5">
						{column.value(row)}
						{#if row.stock_level}
							{@const stock = stockBadge(row.stock_level, true)}
							<Badge tone={stock.tone} title={row.stock_level === 'negative' ? ingredientText.negativeStockHint : undefined}>{stock.label}</Badge>
						{/if}
						{#if row.is_dormant}<Badge tone="neutral" title={ingredientText.idleHint}>{ingredientText.idle}</Badge>{/if}
					</span>
				{:else if column.key === 'status'}
					<Badge tone={row.is_active ? 'success' : 'neutral'}>{column.value(row)}</Badge>
				{:else}
					{column.value(row)}
				{/if}
			{/snippet}
		</DataTable>
		<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
			<Pager page={ingredients.page} total={ingredients.total} unit="bahan" disabled={ingredients.loading} onchange={(page) => ingredients.setPage(page)} />
		</div>
	{/if}
</Card>

<BulkActions
	selection={ingredients.selection}
	noun="bahan"
	bind:removing={ingredients.bulkRemoveOpen}
	bind:changing={ingredients.changeOpen}
	fields={changeFields}
	onchange={(changes) => void ingredients.changeSelected(changes)}
	busy={ingredients.busy}
	error={ingredients.actionError}
	onremove={() => void ingredients.removeSelected()}
	oncancel={() => ingredients.closeDialogs()}
>
	{ingredientText.bulkRemoveNote}
</BulkActions>

{#if ingredients.catalogOpen}
	<CatalogDialog {ingredients} />
{/if}
