<script lang="ts">
	import { emptyText } from '$lib/text/empty';
	import { sopDraftPath, sopEditPath } from '$lib/nav/pages';
	import { goto } from '$app/navigation';
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import SortableList from '$lib/components/sortable/SortableList.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { formatDateTime } from '$lib/format/datetime';
	import { branchOf, sopColumns } from '../columns';
	import type { SopState } from '../sop.svelte';
	import { sopText } from '$lib/text/sop';
	import { format } from '$lib/text/format';

	let { sop }: { sop: SopState } = $props();

	const columns = sopColumns;
</script>

{#if sop.actionError}
	<Banner tone="danger" icon="alert-triangle">{sop.actionError}</Banner>
{/if}

{#if sop.drafts.length > 0}
	<Card flush>
		<CardHeader divided title={sopText.newDrafts} description={sopText.newDraftsDescription} />
		<ul class="flex flex-col divide-y divide-slate-100">
			{#each sop.drafts as draft (draft.id)}
				<li>
					<a href={sopDraftPath(draft.id)} class="flex flex-wrap items-center justify-between gap-3 px-4 py-3 hover:bg-brand-soft tablet:px-5">
						<div class="min-w-0">
							<p class="text-sm font-semibold text-slate-800 wrap-break-word">{draft.title || sopText.untitled}</p>
							<p class="text-xs text-slate-500">{format(sopText.savedAt, { time: formatDateTime(draft.updated_at) })}</p>
						</div>
						<span class="flex items-center gap-1 text-xs font-semibold text-brand">{sopText.resume}<i class="ti ti-chevron-right" aria-hidden="true"></i></span>
					</a>
				</li>
			{/each}
		</ul>
	</Card>
{/if}

<Card flush>
	<CardHeader divided title={sopText.listTitle} description={sop.ordering ? sopText.orderDescription : sopText.listDescription}>
		{#snippet actions()}
			{#if sop.ordering}
				<CancelButton small compact onclick={() => sop.cancelOrdering()} />
				<Button label={sopText.saveOrder} icon="device-floppy" variant="primary" compact disabled={sop.busy} onclick={() => void sop.saveOrder()} />
			{:else if sop.canOrder && sop.items.length > 1}
				<Button label={sopText.arrange} icon="arrows-sort" variant="tertiary" small compact onclick={() => void sop.startOrdering()} />
			{/if}
		{/snippet}
	</CardHeader>
	{#if sop.items.length === 0}
		<Notice text={emptyText.sop.text} />
	{:else if sop.ordering}
		<SortableList bind:items={sop.order} key={(row) => row.id} label={(row) => row.title}>
			{#snippet row(item)}
				<p class="text-sm font-semibold text-slate-800 wrap-break-word">{item.title}</p>
				<p class="text-xs text-slate-500">{branchOf(item)}</p>
			{/snippet}
		</SortableList>
	{:else}
		<DataTable sort={sop.sort} {columns} rows={sop.items} rowKey={(row) => row.id} loading={sop.loading} trailing="status" onopen={(row) => void goto(sopEditPath(row.id))}>
			{#snippet first(row)}
				<span class="block">{row.title}</span>
				{#if row.has_draft}<Badge tone="warning">{sopText.unsavedDraft}</Badge>{/if}
			{/snippet}
			{#snippet cell(row, column)}
				{#if column.key === 'status'}
					<Badge tone={row.active ? 'success' : 'warning'}>{column.value(row)}</Badge>
				{:else if column.key === 'cabang'}
					<Badge tone={row.outlet_id ? 'info' : 'neutral'}>{column.value(row)}</Badge>
				{:else}
					{column.value(row)}
				{/if}
			{/snippet}
		</DataTable>
	{/if}
</Card>
