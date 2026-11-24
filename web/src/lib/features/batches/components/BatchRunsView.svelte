<script lang="ts">
	import { goto } from '$app/navigation';
	import { batchRunPath } from '$lib/nav/pages';
	import Badge from '$lib/components/card/Badge.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import ListSearch from '$lib/components/filter/ListSearch.svelte';
	import { noMatchText } from '$lib/components/filter/no-match';
	import Pager from '$lib/components/pager/Pager.svelte';
	import SkeletonList from '$lib/components/skeleton/SkeletonList.svelte';
	import { BRANCH_SORT, withBranchColumn } from '$lib/components/table/branch-column';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { formatDateTime } from '$lib/format/datetime';
	import { actionText } from '$lib/text/actions';
	import { batchRunText } from '$lib/text/batch-runs';
	import { runColumns } from '../run-columns';
	import type { RunsState } from '../runs.svelte';

	let { runs }: { runs: RunsState } = $props();

	const columns = $derived(withBranchColumn(runColumns, runs.filters.allBranches, BRANCH_SORT));
</script>

<Card flush>
	<CardHeader divided title={batchRunText.listTitle} description={batchRunText.listDescription} />
	<ListSearch value={runs.search} placeholder={batchRunText.searchPlaceholder} label={batchRunText.searchLabel} onsearch={(query) => runs.setSearch(query)} />
	{#if runs.error}
		<div class="p-4">
			<Banner tone="danger" icon="alert-triangle" title={batchRunText.loadFailedTitle}>
				{runs.error}
				{#snippet action()}
					<Button label={actionText.retry} onclick={() => void runs.load()} />
				{/snippet}
			</Banner>
		</div>
	{:else if runs.loading && !runs.loaded}
		<SkeletonList rows={4} label={batchRunText.loading} />
	{:else if runs.items.length === 0}
		<Notice text={noMatchText(batchRunText.unit, runs.search !== '', runs.filters.count > 0) ?? batchRunText.empty} />
	{:else}
		<DataTable sort={runs.sort} {columns} rows={runs.items} rowKey={(row) => row.id} loading={runs.loading} trailing="problems" onopen={(row) => void goto(batchRunPath(row.id))}>
			{#snippet cell(row, column)}
				{#if column.key === 'problems'}
					<Badge tone={row.problems > 0 ? 'danger' : 'success'}>{column.value(row)}</Badge>
				{:else if column.key === 'change' && row.last_action}
					<Badge tone={row.cancelled ? 'danger' : 'warning'} title={row.fixed_at ? formatDateTime(row.fixed_at) : undefined}>{column.value(row)}</Badge>
				{:else if column.key === 'followUp' && row.follow_up_total > 0}
					<Badge tone={row.follow_up_open > 0 ? 'warning' : 'success'}>{column.value(row)}</Badge>
				{:else if column.key === 'kind'}
					<Badge tone={row.kind === 'routine' ? 'brand' : 'neutral'}>{column.value(row)}</Badge>
				{:else}
					{column.value(row)}
				{/if}
			{/snippet}
		</DataTable>
		<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
			<Pager page={runs.page} total={runs.total} unit={batchRunText.unit} disabled={runs.loading} onchange={(page) => runs.setPage(page)} />
		</div>
	{/if}
</Card>
