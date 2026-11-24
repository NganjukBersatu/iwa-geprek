<script lang="ts">
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { formatRupiah, formatRupiahShort } from '$lib/format/currency';
	import type { CashierRow } from '$lib/api/types';
	import type { ListSort } from '$lib/components/table/list-sort.svelte';
	import { cashierColumns } from '../columns';
	import { dashboardCardText } from '$lib/text/dashboard-cards';
	import { format } from '$lib/text/format';

	let { cashiers, sort }: { cashiers: CashierRow[]; sort: ListSort } = $props();

	const columns = cashierColumns;
</script>

<Card flush>
	<CardHeader divided title={dashboardCardText.cashierPerformance} description={format(dashboardCardText.cashiersOnDuty, { count: cashiers.length })} icon="users" tone="brand" />
	<DataTable {sort} {columns} rows={cashiers} rowKey={(row) => row.cashier_id} trailing="selisih">
		{#snippet first(row)}
			<span class="flex flex-col">
				<span class="font-medium text-slate-800">{row.username}</span>
				<span class="text-slate-500">{format(dashboardCardText.shiftsClosed, { count: row.session_count })}</span>
			</span>
		{/snippet}
		{#snippet cell(row, column)}
			{#if column.key === 'transaksi'}
				<span class="flex flex-col">
					<span>{row.transaction_count}</span>
					{#if row.voided_count > 0}<span class="text-danger-700">{format(dashboardCardText.voidedCount, { count: row.voided_count })}</span>{/if}
				</span>
			{:else if column.key === 'penjualan'}
				<span class="flex flex-col">
					<span class="font-semibold text-slate-800">{formatRupiah(row.sales_total)}</span>
					<span class="text-slate-500">{format(dashboardCardText.cashAndNonCashLower, { cash: formatRupiahShort(row.cash_total), nonCash: formatRupiahShort(row.non_cash_total) })}</span>
				</span>
			{:else}
				{column.value(row)}
			{/if}
		{/snippet}
	</DataTable>
	<p class="border-t border-slate-100 px-4 py-3 text-xs text-slate-500 tablet:px-5">
		{dashboardCardText.differenceNote}
		<span class="text-danger-700">{dashboardCardText.red}</span> {dashboardCardText.redMeaning}
		<span class="text-warning-700">{dashboardCardText.yellow}</span> {dashboardCardText.yellowMeaning}
	</p>
</Card>
