<script lang="ts">
	import { goto } from '$app/navigation';
	import { expenseNewPath, expensePath } from '$lib/nav/pages';
	import type { SessionHistoryRow } from '$lib/api/types';
	import Button from '$lib/components/button/Button.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import ListToolbar from '$lib/components/filter/ListToolbar.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { sessionExpenseColumns } from '../columns';
	import type { SessionDetailState } from '../session-detail.svelte';
	import { sessionDetailText } from '$lib/text/session-detail';
	import { format } from '$lib/text/format';

	let { session, row }: { session: SessionDetailState; row: SessionHistoryRow } = $props();

	const columns = sessionExpenseColumns;
</script>

<ListToolbar
	value={session.search}
	placeholder={sessionDetailText.searchExpensesPlaceholder}
	label={sessionDetailText.searchExpenses}
	filters={session.expenseFilters}
	shown={session.visibleExpenses.length}
	total={session.expenses?.length ?? 0}
	unit="pengeluaran"
	onsearch={(query) => session.setSearch(query)}
>
	{#snippet actions()}
		<Button label={sessionDetailText.addExpense} icon="plus" onclick={() => void goto(expenseNewPath(row.id))} />
	{/snippet}
</ListToolbar>

{#if session.expensesError}
	<Notice text={format(sessionDetailText.expensesLoadFailedDetail, { detail: session.expensesError })} />
{:else if session.expenses === null}
	<Notice loading text={sessionDetailText.expensesLoading} />
{:else if session.visibleExpenses.length === 0}
	<Notice text={session.expenses.length === 0 ? sessionDetailText.noExpenses : sessionDetailText.noExpensesMatch} />
{:else}
	<DataTable sort={session.expenseSort} {columns} rows={session.visibleExpenses} rowKey={(item) => item.id} trailing="jumlah" onopen={(item) => void goto(expensePath(item.id))} />
{/if}
