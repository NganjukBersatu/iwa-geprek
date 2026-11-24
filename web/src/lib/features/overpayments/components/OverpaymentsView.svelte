<script lang="ts">
	import type { OverpaymentReport } from '$lib/api/types';
	import { goto } from '$app/navigation';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import SummaryCard from '$lib/components/card/SummaryCard.svelte';
	import Pager from '$lib/components/pager/Pager.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { formatNumber, formatRupiah } from '$lib/format/currency';
	import { orderPath } from '$lib/nav/pages';
	import { overpaymentColumns } from '../columns';
	import type { OverpaymentsState } from '../overpayments.svelte';
	import { termText } from '$lib/text/terms';
	import { overpaymentText } from '$lib/text/overpayments';

	let { data, overpayments }: { data: OverpaymentReport; overpayments: OverpaymentsState } = $props();

	const columns = $derived(overpaymentColumns(overpayments.allBranches));
</script>

<div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
	<SummaryCard label={termText.transaction} caption={overpaymentText.summaryCaption} value="{formatNumber(data.count, 0)} transaksi" icon="receipt" accent={data.count > 0 ? 'accent' : 'green'} />
	<SummaryCard label={overpaymentText.totalExcess} caption={overpaymentText.totalCaption} value={formatRupiah(data.total_amount)} icon="cash-banknote" accent="accent" />
</div>

<Card flush>
	<CardHeader divided title={overpaymentText.listTitle} description={overpaymentText.listDescription} />
	{#if data.rows.length === 0}
		<Notice text={overpaymentText.noOverpayments} />
	{:else}
		<DataTable {columns} rows={data.rows} rowKey={(row) => row.id} trailing="kelebihan" loading={overpayments.loading} sort={overpayments.sort} onopen={(row) => row.session_id && void goto(orderPath(row.session_id, row.order_id))}>
			{#snippet first(row)}
				<span class="block">{columns[0]!.value(row)}</span>
				<span class="block max-w-xs truncate text-xs font-normal text-slate-500">{row.purchases}</span>
			{/snippet}
			{#snippet cell(row, column)}
				{#if column.key === 'status'}
					<Badge tone={row.voided ? 'danger' : 'success'}>{column.value(row)}</Badge>
				{:else}
					{column.value(row)}
				{/if}
			{/snippet}
		</DataTable>
		<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
			<Pager page={data.page} total={data.count} unit="transaksi" disabled={overpayments.loading} onchange={(page) => overpayments.setPage(page)} />
		</div>
	{/if}
</Card>
