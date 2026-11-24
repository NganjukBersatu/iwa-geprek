<script lang="ts">
	import PageButton from '$lib/components/button/PageButton.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import ListSearch from '$lib/components/filter/ListSearch.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { PAGES } from '$lib/nav/pages';
	import { categoryText } from '$lib/text/category';
	import type { CategoryState } from '../category.svelte';
	import { unsoldColumns } from '../columns';
	import { categoryReportText } from '$lib/text/category-report';
	import { format } from '$lib/text/format';

	let { category }: { category: CategoryState } = $props();

	const rows = $derived(category.unsold);

	const columns = unsoldColumns;
</script>

<Card flush>
	<CardHeader divided title={categoryReportText.notSoldInPeriod} description={format(categoryReportText.unsoldCaption, { count: rows.length })} />
	<ListSearch value={category.search} placeholder={categoryReportText.searchPlaceholder} label={categoryReportText.search} onsearch={(query) => category.setSearch(query)} />
	{#if rows.length === 0}
		{@const reason = category.unsoldEmptyReason}
		{#if reason}
			<Notice text={categoryText.unsoldEmpty[reason]} />
			{#if reason === 'noMenu'}
				<div class="flex justify-center pb-6"><PageButton page={PAGES.menu} /></div>
			{/if}
		{/if}
	{:else}
		<div class="max-h-130 overflow-y-auto">
			<DataTable sort={category.unsoldSort} {columns} {rows} rowKey={(row) => row.menu_item_id}>
				{#snippet first(row)}
					{row.name}
					{#if !row.is_available}<Badge>{categoryReportText.hidden}</Badge>{/if}
				{/snippet}
			</DataTable>
		</div>
	{/if}
</Card>
