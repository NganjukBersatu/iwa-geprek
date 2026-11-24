<script lang="ts">
	import { goto } from '$app/navigation';
	import { recipePath } from '$lib/nav/pages';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import ListSearch from '$lib/components/filter/ListSearch.svelte';
	import { noMatchText } from '$lib/components/filter/no-match';
	import Notice from '$lib/components/card/Notice.svelte';
	import Pager from '$lib/components/pager/Pager.svelte';
	import { withBranchColumn } from '$lib/components/table/branch-column';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import type { Column } from '$lib/components/table/types';
	import { EMPTY_VALUE, formatPercentPlain, formatRupiah } from '$lib/format/currency';
	import type { RecipeRow, RecipesState } from '../recipes.svelte';
	import { termText } from '$lib/text/terms';
	import { recipeText } from '$lib/text/recipes';

	let { recipes }: { recipes: RecipesState } = $props();

	const money = (value: unknown) => (value === null || value === undefined ? EMPTY_VALUE : formatRupiah(value as string));

	const baseColumns = $derived<Column<RecipeRow>[]>([
		{ key: 'menu', label: termText.menu, align: 'left', value: (row) => row.menu_name },
		{ key: 'kategori', label: termText.category, align: 'left', value: (row) => row.category_name ?? EMPTY_VALUE },
		{ key: 'harga', label: recipeText.sellingPrice, value: (row) => formatRupiah(row.price) },
		...(recipes.seesCost
			? [
					{ key: 'hpp', label: recipeText.finalCost, value: (row: RecipeRow) => money(row.final_cost) },
					{
						key: 'margin',
						label: recipeText.margin,
						value: (row: RecipeRow) => (row.margin_percent === null ? EMPTY_VALUE : formatPercentPlain(row.margin_percent)),
						class: (row: RecipeRow) => (row.margin !== null && Number(row.margin) < 0 ? 'font-semibold text-danger-700' : '')
					}
				]
			: [])
	]);
	const columns = $derived(withBranchColumn(baseColumns, recipes.filters.allBranches));
</script>

<Card flush>
	<CardHeader divided title={recipeText.masterTitle} description={recipeText.masterDescription} />
	<ListSearch value={recipes.search} placeholder={recipeText.searchPlaceholder} label={recipeText.search} onsearch={(query) => recipes.setSearch(query)} />
	{#if recipes.items.length === 0}
		<Notice text={noMatchText('menu', recipes.search !== '', recipes.filters.count > 0) ?? recipeText.noMenus} />
	{:else}
		<DataTable {columns} rows={recipes.items} rowKey={(row) => row.id} loading={recipes.loading} onopen={(row) => void goto(recipePath(row.id))}>
			{#snippet first(row)}
				<span class="inline-flex items-center gap-2">
					<span>{row.menu_name}</span>
					{#if !row.has_recipe}<Badge tone="warning">{recipeText.noRecipe}</Badge>{/if}
				</span>
			{/snippet}
		</DataTable>
		<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
			<Pager page={recipes.page} total={recipes.total} unit="menu" disabled={recipes.loading} onchange={(page) => recipes.setPage(page)} />
		</div>
	{/if}
</Card>
