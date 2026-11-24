<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import ShareBar from '$lib/components/chart/ShareBar.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import type { CategoryState } from '../category.svelte';
	import { categoryColumns } from '../columns';
	import { categoryReportText } from '$lib/text/category-report';
	import { format } from '$lib/text/format';

	let { category }: { category: CategoryState } = $props();

	const rows = $derived(category.data?.categories ?? []);

	const columns = categoryColumns;
</script>

<Card flush>
	<CardHeader divided title={categoryReportText.perCategory} description={format(categoryReportText.categoryRevenueCaption, { period: category.periodLabel })} />
	{#if rows.length === 0}
		<Notice text={categoryReportText.noSales} />
	{:else}
		<DataTable sort={category.sort} {columns} {rows} rowKey={(row) => row.category} trailing="omzet">
			{#snippet first(row)}
				<span class="block">{row.category}</span>
				<span class="block text-xs font-normal text-slate-500">{format(controlText.menusCount, { count: row.menu_count })}</span>
				<ShareBar value={Number(row.revenue_percent)} class="mt-1.5" />
			{/snippet}
		</DataTable>
	{/if}
</Card>
