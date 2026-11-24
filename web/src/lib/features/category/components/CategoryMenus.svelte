<script lang="ts">
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { categoryReportText } from '$lib/text/category-report';
	import { format } from '$lib/text/format';
	import type { CategoryState } from '../category.svelte';
	import { menuColumns } from '../columns';
	import ProfitCell from './ProfitCell.svelte';

	let { category, name }: { category: CategoryState; name: string } = $props();

	const rows = $derived(category.menusOf(name));
</script>

<section>
	<h3 class="mb-1.5 text-xs font-semibold text-slate-600">{format(categoryReportText.menusInCategory, { category: name })}</h3>
	{#if rows.length === 0}
		<p class="text-xs text-slate-500">{categoryReportText.noMenuSales}</p>
	{:else}
		<DataTable sort={category.menuSort} columns={menuColumns} {rows} rowKey={(row) => row.menu_item_id ?? row.name} trailing="omzet">
			{#snippet cell(row, column)}
				{#if column.key === 'laba'}
					<ProfitCell profit={row.profit} complete={row.cost_complete} />
				{:else}
					{column.value(row)}
				{/if}
			{/snippet}
		</DataTable>
	{/if}
</section>
