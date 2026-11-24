<script lang="ts">
	import { branchDetailText } from '$lib/text/branch-detail';
	import { format } from '$lib/text/format';
	import { goto } from '$app/navigation';
	import { branchNewPath, branchPath } from '$lib/nav/pages';
	import { emptyText } from '$lib/text/empty';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import type { BranchesState } from '../branches.svelte';
	import { branchColumns } from '../columns';
	import BranchForm from './BranchForm.svelte';
	import { branchText } from '$lib/text/branches';

	let { branches }: { branches: BranchesState } = $props();

	const columns = branchColumns;
</script>

<Card flush>
	<CardHeader divided title={branchText.listTitle} description={branchText.listDescription} />
	{#if branches.items.length === 0}
		<Notice title={emptyText.branches.title} text={emptyText.branches.text}/>
	{:else}
		<DataTable sort={branches.sort} {columns} rows={branches.items} rowKey={(row) => row.id} loading={branches.loading} trailing="status" onopen={(row) => void goto(branchPath(row.id))}>
			{#snippet first(row)}
				<span class="block">{row.name}</span>
				<span class="block text-xs font-normal text-slate-500">{[row.code, row.receipt_number ? format(branchText.receiptNumber, { number: row.receipt_number }) : ''].filter(Boolean).join(' · ') || branchDetailText.noCode}</span>
			{/snippet}
			{#snippet cell(row, column)}
				{#if column.key === 'status'}
					<Badge tone={row.is_active ? 'success' : 'neutral'}>{column.value(row)}</Badge>
				{:else if column.key === 'titik' && row.latitude === null}
					<span class="text-warning-700">{column.value(row)}</span>
				{:else}
					{column.value(row)}
				{/if}
			{/snippet}
		</DataTable>
	{/if}
</Card>

