<script lang="ts">
	import { goto } from '$app/navigation';
	import { batchPath } from '$lib/nav/pages';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import ListSearch from '$lib/components/filter/ListSearch.svelte';
	import { noMatchText } from '$lib/components/filter/no-match';
	import Pager from '$lib/components/pager/Pager.svelte';
	import SkeletonList from '$lib/components/skeleton/SkeletonList.svelte';
	import { BRANCH_SORT, withBranchColumn } from '$lib/components/table/branch-column';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { actionText } from '$lib/text/actions';
	import { batchText } from '$lib/text/batches';
	import { format } from '$lib/text/format';
	import type { BatchesState } from '../batches.svelte';
	import { TARGET_USER } from '../constants';
	import ShiftCodeBadge from '$lib/components/card/ShiftCodeBadge.svelte';

	let { batches }: { batches: BatchesState } = $props();

	const text = $derived(batches.text);
	const columns = $derived(withBranchColumn(batches.columns, batches.filters.allBranches, BRANCH_SORT));
</script>

<Card flush>
	<CardHeader divided title={format(batchText.listTitleOf, { noun: text.noun })} description={text.listHint} />
	<ListSearch value={batches.search} placeholder={batchText.searchPlaceholder} label={format(batchText.searchLabel, { noun: text.noun })} onsearch={(query) => batches.setSearch(query)} />
	{#if batches.error}
		<div class="p-4">
			<Banner tone="danger" icon="alert-triangle" title={format(batchText.loadFailedOf, { title: text.title })}>
				{batches.error}
				{#snippet action()}
					<Button label={actionText.retry} onclick={() => void batches.load()} />
				{/snippet}
			</Banner>
		</div>
	{:else if batches.loading && !batches.loaded}
		<SkeletonList rows={4} label={format(batchText.loadingOf, { noun: text.noun })} />
	{:else if batches.items.length === 0}
		{@const noMatch = noMatchText(text.noun, batches.search !== '', batches.filters.count > 0)}
		{#if noMatch}
			<Notice text={noMatch} />
		{:else}
			<Notice text={text.empty} />
		{/if}
	{:else}
		<DataTable sort={batches.sort} {columns} rows={batches.items} rowKey={(row) => row.id} loading={batches.loading} trailing="status" onopen={(row) => void goto(batchPath(row.id))}>
			{#snippet cell(row, column)}
				{#if column.key === 'status'}
					<Badge tone={row.is_active ? 'success' : 'warning'}>{column.value(row)}</Badge>
				{:else if column.key === 'recipient' && row.target === TARGET_USER}
					{#if row.user.length === 0}
						<Badge tone="warning">{batchText.noRecipient}</Badge>
					{:else}
						<span class="block max-w-xs truncate" title={column.value(row)}>{format(batchText.peopleCount, { count: row.user.length, names: column.value(row) })}</span>
					{/if}
				{:else if column.key === 'recipient'}
					<span class="flex flex-wrap gap-1">
						{#each row.shift_codes as code (code.id)}
							<ShiftCodeBadge {code} />
						{/each}
					</span>
				{:else}
					{column.value(row)}
				{/if}
			{/snippet}
		</DataTable>
		<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
			<Pager page={batches.page} total={batches.total} unit={text.noun} disabled={batches.loading} onchange={(page) => batches.setPage(page)} />
		</div>
	{/if}
</Card>
