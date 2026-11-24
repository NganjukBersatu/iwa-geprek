<script lang="ts">
	import { goto } from '$app/navigation';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import Pager from '$lib/components/pager/Pager.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { branchPeriodPath } from '$lib/nav/pages';
	import { branchPeriodText as text } from '$lib/text/branch-periods';
	import type { BranchPeriodsState } from '../branch-periods.svelte';
	import { periodColumns, periodSource } from '../columns';

	let { periods, onedit }: { periods: BranchPeriodsState; onedit?: () => void } = $props();

	const visible = $derived(periods.visible);
</script>

<Card flush>
	<CardHeader divided title={text.sectionTitle} description={text.sectionDescription}>
		{#snippet actions()}
			{#if onedit}
				<Button label={text.editRunning} icon="calendar-cog" compact onclick={onedit} />
			{/if}
		{/snippet}
	</CardHeader>
	{#if periods.items.length === 0}
		<Notice text={text.empty} />
	{:else}
		<DataTable columns={periodColumns} rows={visible.rows} rowKey={(row) => row.id} loading={periods.loading} trailing="status" onopen={(row) => void goto(branchPeriodPath(row.outlet_id, row.start))}>
			{#snippet cell(row, column)}
				{#if column.key === 'status'}
					<Badge tone={row.running ? 'success' : 'neutral'}>{column.value(row)}</Badge>
				{:else if column.key === 'source'}
					<Badge tone={periodSource(row).tone}>{column.value(row)}</Badge>
				{:else}
					{column.value(row)}
				{/if}
			{/snippet}
		</DataTable>
		<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
			<Pager page={visible.page} total={periods.total} unit={text.unit} disabled={periods.loading} onchange={(page) => periods.setPage(page)} />
		</div>
	{/if}
</Card>
