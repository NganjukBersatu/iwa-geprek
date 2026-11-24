<script lang="ts">
	import { goto } from '$app/navigation';
	import { expenseNewPath, expensePath } from '$lib/nav/pages';
	import { emptyText } from '$lib/text/empty';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import ListSearch from '$lib/components/filter/ListSearch.svelte';
	import { noMatchText } from '$lib/components/filter/no-match';
	import Notice from '$lib/components/card/Notice.svelte';
	import SummaryCard from '$lib/components/card/SummaryCard.svelte';
	import { whenChanged } from '$lib/stores/when-changed.svelte';
	import DepositedDayWarning from '../../deposits/components/DepositedDayWarning.svelte';
	import Pager from '$lib/components/pager/Pager.svelte';
	import BulkActions from '$lib/components/table/BulkActions.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { formatNumber, formatRupiah } from '$lib/format/currency';
	import type { ExpensesState } from '../expenses.svelte';
	import { expenseColumns } from '../columns';
	import { expenseText } from '$lib/text/expenses';
	import { format } from '$lib/text/format';

	let { expenses }: { expenses: ExpensesState } = $props();

	whenChanged(() => expenses.bulkRemoveOpen, (open) => open && expenses.checkSelected());

	const columns = expenseColumns;

</script>

<div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
	<SummaryCard label={expenseText.totalExpense} caption={format(expenseText.recordsInFilter, { count: formatNumber(expenses.total, 0) })} value={formatRupiah(expenses.totalAmount)} icon="wallet" accent="accent" />
	<SummaryCard label={expenseText.fromCashRevenue} caption={expenseText.reducesDrawerCash} value={formatRupiah(expenses.drawerAmount)} icon="cash" accent="soft" />
</div>

<Card flush>
	<CardHeader divided title={expenseText.listTitle} description={expenseText.listDescription} />
	<ListSearch value={expenses.search} placeholder={expenseText.searchPlaceholder} label={expenseText.search} onsearch={(query) => expenses.setSearch(query)} />
	{#if !expenses.loading && expenses.items.length === 0}
		{@const noMatch = noMatchText('pengeluaran', expenses.search !== '', expenses.filters.count > 0)}
		{#if noMatch}
			<Notice text={noMatch} />
		{:else}
			<Notice title={emptyText.expenses.title} text={emptyText.expenses.text}/>
		{/if}
	{:else}
		<DataTable {columns} rows={expenses.items} rowKey={(row) => row.id} loading={expenses.loading} selection={expenses.selection} trailing="jumlah" sort={expenses.sort} onopen={(row) => void goto(expensePath(row.id))}>
			{#snippet first(row)}
				<span class="inline-flex items-center gap-2">
					<span>{row.item_name}</span>
					{#if row.receipt_url}
						<a href={row.receipt_url} target="_blank" rel="noopener" class="text-brand" aria-label={format(expenseText.viewReceipt, { name: row.item_name })}><i class="ti ti-receipt" aria-hidden="true"></i></a>
					{/if}
					{#if row.session_closed}<Badge tone="neutral">{expenseText.sessionClosed}</Badge>{/if}
				</span>
				{#if row.note || row.buyer}
					<span class="block max-w-xs truncate text-xs font-normal text-slate-500">{[row.buyer, row.note].filter(Boolean).join(' · ')}</span>
				{/if}
			{/snippet}
		</DataTable>
		<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
			<Pager page={expenses.page} total={expenses.total} unit="pengeluaran" disabled={expenses.loading} onchange={(page) => expenses.setPage(page)} />
		</div>
	{/if}
</Card>

<BulkActions
	selection={expenses.selection}
	noun="pengeluaran"
	bind:removing={expenses.bulkRemoveOpen}
	busy={expenses.busy || expenses.warning.checking}
	error={expenses.actionError}
	onremove={() => void expenses.removeSelected()}
	oncancel={() => expenses.closeDialogs()}
>
	{expenseText.bulkRemoveNote}
	<DepositedDayWarning warning={expenses.warning} />
</BulkActions>
