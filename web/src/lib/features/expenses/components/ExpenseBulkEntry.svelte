<script lang="ts">
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import type { ExpenseCreate } from '$lib/api/types';
	import BulkEntryDialog from '$lib/components/dialog/BulkEntryDialog.svelte';
	import type { Field } from '$lib/components/form/types';
	import { PAGES } from '$lib/nav/pages';
	import { FUND_SOURCES } from '../../finance/fund-sources';
	import { termText } from '$lib/text/terms';
	import { expenseText } from '$lib/text/expenses';

	const entryColumns: Field[] = [
		{ key: 'item_name', label: expenseText.itemName, required: true },
		{ key: 'amount', label: expenseText.priceRupiah, kind: 'number', required: true },
		{ key: 'fund_source', label: expenseText.fundingSource, kind: 'select', required: true, options: Object.entries(FUND_SOURCES).map(([value, label]) => ({ value, label })) },
		{ key: 'note', label: termText.note },
		{ key: 'buyer', label: expenseText.buyer }
	];

	function createMany(rows: Record<string, string | number>[], outletId: string) {
		const items: ExpenseCreate[] = rows.map((row) => ({
			item_name: String(row['item_name']),
			amount: String(row['amount']),
			fund_source: String(row['fund_source']) as ExpenseCreate['fund_source'],
			note: row['note'] ? String(row['note']) : null,
			buyer: row['buyer'] ? String(row['buyer']) : null
		}));
		return api.expenses.bulk.createIn(outletId, items);
	}
</script>

<BulkEntryDialog
	asPage
	title={expenseText.bulkTitle}
	hint={expenseText.bulkHint}
	columns={entryColumns}
	withBranch
	submit={createMany}
	submitLabel="Simpan semua pengeluaran"
	onclose={() => void goto(PAGES.expenses.path)}
/>
