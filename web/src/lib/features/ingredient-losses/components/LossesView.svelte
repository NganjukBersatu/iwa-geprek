<script lang="ts">
	import { goto } from '$app/navigation';
	import { lossNewPath, lossPath } from '$lib/nav/pages';
	import { emptyText } from '$lib/text/empty';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import ListSearch from '$lib/components/filter/ListSearch.svelte';
	import { noMatchText } from '$lib/components/filter/no-match';
	import Notice from '$lib/components/card/Notice.svelte';
	import SummaryCard from '$lib/components/card/SummaryCard.svelte';
	import Pager from '$lib/components/pager/Pager.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { formatNumber } from '$lib/format/currency';
	import type { IngredientLossesState } from '../ingredient-losses.svelte';
	import { WASTE } from '../kinds';
	import { lossColumns } from '../columns';
	import { ingredientLossText } from '$lib/text/ingredient-losses';
	import { format } from '$lib/text/format';

	let { losses }: { losses: IngredientLossesState } = $props();

	const isWaste = $derived(losses.kind === WASTE);

	const columns = $derived(lossColumns(losses.kind));
</script>


{#if losses.actionError}
	<Banner tone="warning" icon="alert-triangle">{losses.actionError}</Banner>
{/if}

{#if isWaste}
	<div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
		<SummaryCard label={ingredientLossText.negligence} caption={ingredientLossText.negligenceExamples} value={formatNumber(losses.humanErrors, 0)} icon="alert-triangle" accent="red" />
		<SummaryCard label={ingredientLossText.naturalLoss} caption={ingredientLossText.naturalLossExamples} value={formatNumber(losses.natural, 0)} icon="leaf" accent="plain" />
	</div>
{/if}

<Card flush>
	<CardHeader divided title={isWaste ? ingredientLossText.damagedListTitle : ingredientLossText.rndListTitle} description={isWaste ? ingredientLossText.damagedListDescription : ingredientLossText.rndListDescription} />
	<ListSearch value={losses.search} placeholder={ingredientLossText.searchPlaceholder} label={ingredientLossText.search} onsearch={(query) => losses.setSearch(query)} />
	{#if !losses.loading && losses.items.length === 0}
		{@const noMatch = noMatchText('catatan', losses.search !== '', losses.filters.count > 1)}
		{#if noMatch}
			<Notice text={noMatch} />
		{:else}
			<Notice title={emptyText.losses.title} text={emptyText.losses.text}/>
		{/if}
	{:else}
		<DataTable {columns} rows={losses.items} rowKey={(row) => row.id} loading={losses.loading} sort={losses.sort} onopen={(row) => void goto(lossPath(row.id))}>
			{#snippet first(row)}
				<span class="inline-flex items-center gap-2">
					<span>{row.ingredient_name}</span>
					{#if row.proof_url}
						<a href={row.proof_url} target="_blank" rel="noopener" class="text-brand" aria-label={format(ingredientLossText.viewProof, { name: row.ingredient_name })}><i class="ti ti-photo" aria-hidden="true"></i></a>
					{/if}
				</span>
				{#if row.note}<span class="block max-w-xs truncate text-xs font-normal text-slate-500">{row.note}</span>{/if}
			{/snippet}
			{#snippet cell(row, column)}
				{#if column.key === 'sebab' && row.cause_label}
					<Badge tone={row.human_error ? 'danger' : 'neutral'}>{row.cause_label}</Badge>
				{:else}
					{column.value(row)}
				{/if}
			{/snippet}
		</DataTable>
		<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
			<Pager page={losses.page} total={losses.total} unit="catatan" disabled={losses.loading} onchange={(page) => losses.setPage(page)} />
		</div>
	{/if}
</Card>
