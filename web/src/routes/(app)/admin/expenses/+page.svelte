<script lang="ts">
	import { expenseBulkPath, expenseNewPath } from '$lib/nav/pages';
	import { goto } from '$app/navigation';
	import AddButton from '$lib/components/button/AddButton.svelte';
	import MoreButton from '$lib/components/button/MoreButton.svelte';
	import ExpensesView from '$lib/features/expenses/components/ExpensesView.svelte';
	import { ExpensesState } from '$lib/features/expenses/expenses.svelte';
	import { expenseColumns } from '$lib/features/expenses/columns';
	import ManageShell from '$lib/features/manage/ManageShell.svelte';
	import { termText } from '$lib/text/terms';
	import { pageText } from '$lib/text/pages';

	const expenses = new ExpensesState();
</script>

<ManageShell manage={expenses} filters={expenses.filters} title={termText.expense} description={pageText.expensesDescription} loadingText="Memuat pengeluaran...">
	{#snippet actions()}
		<AddButton label={pageText.recordExpense} onone={() => void goto(expenseNewPath())} onmany={() => void goto(expenseBulkPath())} />
		<MoreButton selection={expenses.selection} exporter={{ title: termText.expense, columns: expenseColumns, rows: () => expenses.exportRows() }} />
	{/snippet}
	{#snippet children()}
		<ExpensesView {expenses} />
	{/snippet}
</ManageShell>
