<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { api } from '$lib/api';
	import type { Expense, ExpenseReceipt, SessionChoice, SessionHistoryRow } from '$lib/api/types';
	import { EXPENSE_SESSION_PARAM, PAGES, expensePath, sessionPath } from '$lib/nav/pages';
	import { createText } from '$lib/text/record-detail';
	import RecordCreateView from '../../record-detail/components/RecordCreateView.svelte';
	import { RecordCreateState } from '../../record-detail/record-create.svelte';
	import { recordedSummary } from '../receipt';
	import ExpenseForm from './ExpenseForm.svelte';
	import { expenseText } from '$lib/text/expenses';

	type ExpenseSave = { body: ExpenseReceipt; receipt: File | null; outletId: string };
	/** Opened from a session's page, the expense is bound to that session and its branch. */
	type ExpenseContext = { session: SessionHistoryRow | null };

	const sessionId = page.url.searchParams.get(EXPENSE_SESSION_PARAM);
	const startOf = (row: SessionHistoryRow): SessionChoice => ({ id: row.id, outlet_id: row.outlet_id, business_day: row.business_day, cashier_username: row.cashier_username, shift_code: row.shift_code, opened_at: row.opened_at, running: row.running, has_shopping_fund: false });

	// A receipt can hold several items, so one save makes one or more expenses; a single one is opened, several return to the list.
	const create = new RecordCreateState<Expense[], ExpenseSave, ExpenseContext>({
		context: async () => ({ session: sessionId ? await api.sessions.historyDetail(sessionId) : null }),
		create: ({ body, receipt, outletId }) => api.expenses.recordReceipt(outletId, body, receipt),
		name: (saved) => saved[0]?.item_name ?? '',
		message: (saved) => `${recordedSummary(saved)}${saved[0]?.session_closed ? expenseText.sessionRecalculatedNote : ''}`,
		after: (saved) => (sessionId ? sessionPath(sessionId) : saved.length === 1 && saved[0] ? expensePath(saved[0].id) : PAGES.expenses.path),
		text: createText('pengeluaran')
	});
</script>

<RecordCreateView {create} back={PAGES.expenses}>
	{#snippet form(props)}
		<ExpenseForm expense={null} startSession={props.context?.session ? startOf(props.context.session) : null} fixedOutlet={props.context?.session?.outlet_id ?? ''} busy={props.busy} error={props.error} fieldErrors={props.fieldErrors} onrecord={(body, receipt, outletId) => props.onsave({ body, receipt, outletId })} onclose={() => (sessionId ? void goto(sessionPath(sessionId)) : props.onclose())} />
	{/snippet}
</RecordCreateView>
