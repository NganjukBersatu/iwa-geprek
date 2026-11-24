<script lang="ts">
	import { goto } from '$app/navigation';
	import { receiptNewPath, receiptPath } from '$lib/nav/pages';
	import { emptyText } from '$lib/text/empty';
	import Button from '$lib/components/button/Button.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import ListSearch from '$lib/components/filter/ListSearch.svelte';
	import { noMatchText } from '$lib/components/filter/no-match';
	import Notice from '$lib/components/card/Notice.svelte';
	import Pager from '$lib/components/pager/Pager.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import type { IngredientReceiptsState } from '../ingredient-receipts.svelte';
	import { receiptColumns } from '../columns';
	import { ingredientReceiptText } from '$lib/text/ingredient-receipts';
	import { format } from '$lib/text/format';

	let { receipts }: { receipts: IngredientReceiptsState } = $props();

	const columns = receiptColumns;
</script>


{#if receipts.actionError}
	<Banner tone="warning" icon="alert-triangle">{receipts.actionError}</Banner>
{/if}

<Card flush>
	<CardHeader divided title={ingredientReceiptText.listTitle} description={ingredientReceiptText.listDescription} />
	<ListSearch value={receipts.search} placeholder={ingredientReceiptText.searchPlaceholder} label={ingredientReceiptText.search} onsearch={(query) => receipts.setSearch(query)} />
	{#if !receipts.loading && receipts.items.length === 0}
		{@const noMatch = noMatchText('catatan', receipts.search !== '', receipts.filters.count > 0)}
		{#if noMatch}
			<Notice text={noMatch} />
		{:else}
			<Notice title={emptyText.receipts.title} text={emptyText.receipts.text}/>
		{/if}
	{:else}
		<DataTable {columns} rows={receipts.items} rowKey={(row) => row.id} loading={receipts.loading} trailing="jumlah" sort={receipts.sort} onopen={(row) => void goto(receiptPath(row.id))}>
			{#snippet first(row)}
				<span class="inline-flex items-center gap-2">
					<span>{row.ingredient_name}</span>
					{#if row.proof_url}
						<a href={row.proof_url} target="_blank" rel="noopener" class="text-brand" aria-label={format(ingredientReceiptText.viewProof, { name: row.ingredient_name })}><i class="ti ti-receipt" aria-hidden="true"></i></a>
					{/if}
				</span>
				{#if row.note}<span class="block max-w-xs truncate text-xs font-normal text-slate-500">{row.note}</span>{/if}
			{/snippet}
		</DataTable>
		<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
			<Pager page={receipts.page} total={receipts.total} unit="catatan" disabled={receipts.loading} onchange={(page) => receipts.setPage(page)} />
		</div>
	{/if}
</Card>
