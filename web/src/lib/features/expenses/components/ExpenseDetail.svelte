<script lang="ts">
	import { untrack } from 'svelte';
	import { api } from '$lib/api';
	import type { Expense, ExpenseUpdate } from '$lib/api/types';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import FigureList from '$lib/components/card/FigureList.svelte';
	import { formatDate } from '$lib/date/range';
	import { EMPTY_VALUE, formatRupiah } from '$lib/format/currency';
	import { formatDateTime } from '$lib/format/datetime';
	import { EXPENSE_TABLES } from '$lib/live/tables';
	import { PAGES } from '$lib/nav/pages';
	import { recordText } from '$lib/text/record-detail';
	import DepositedDayWarning from '../../deposits/components/DepositedDayWarning.svelte';
	import { DayWarning } from '../../deposits/day-warning.svelte';
	import { FUND_SOURCES } from '../../finance/fund-sources';
	import RecordDetailView from '../../record-detail/components/RecordDetailView.svelte';
	import { RecordDetailState } from '../../record-detail/record-detail.svelte';
	import { quantityText } from '../receipt';
	import ExpenseForm from './ExpenseForm.svelte';
	import { termText } from '$lib/text/terms';
	import { expenseText } from '$lib/text/expenses';
	import { format } from '$lib/text/format';

	type ExpenseSave = { body: ExpenseUpdate; receipt: File | null };

	let { id }: { id: string } = $props();

	const detail = new RecordDetailState<Expense, ExpenseSave>(untrack(() => id), {
		load: (expenseId) => api.expenses.detail(expenseId),
		update: async (expense, { body, receipt }) => {
			const saved = await api.expenses.update(expense.id, body);
			return receipt ? api.expenses.uploadReceipt(saved.id, receipt) : saved;
		},
		remove: (expense) => api.expenses.remove(expense.id),
		name: (expense) => expense.item_name,
		text: recordText('pengeluaran', PAGES.expenses.label)
	});

	// Deleting changes the money of its day, so the day's state is read as the confirmation opens.
	const warning = new DayWarning();
	$effect(() => {
		const expense = detail.record;
		if (detail.removing && expense) void warning.read([{ outlet_id: expense.outlet_id, day: expense.business_day }]);
		else warning.clear();
	});

	const ingredientText = (expense: Expense) => {
		if (!expense.ingredient_name) return EMPTY_VALUE;
		const amount = [quantityText(expense.quantity), expense.quantity ? expense.unit_name : null].filter(Boolean).join(' ');
		return amount ? `${expense.ingredient_name} · ${amount}` : expense.ingredient_name;
	};
</script>

<RecordDetailView
	{detail}
	back={PAGES.expenses}
	trail={(expense) => [{ label: PAGES.expenses.label, href: PAGES.expenses.path }, { label: expense.item_name }]}
	tables={EXPENSE_TABLES}
	title={(expense) => expense.item_name}
	description={(expense) => `${formatRupiah(expense.amount)} · ${formatDate(expense.business_day)}`}
	removeBusy={warning.checking}
>
	{#snippet badge(expense)}
		{#if expense.session_closed}<Badge tone="neutral">{expenseText.sessionClosed}</Badge>{/if}
	{/snippet}
	{#snippet body(expense)}
		<div class="grid items-stretch gap-4 tablet:gap-6 laptop:grid-cols-[20rem_minmax(0,1fr)]">
			<Card flush>
				<div class="flex h-full flex-col gap-3 bg-brand-soft p-4">
					<span class="text-xs font-medium text-brand-deep">{expenseText.receiptPhoto}</span>
					<div class="flex aspect-4/3 items-center justify-center overflow-hidden rounded-lg bg-brand-tint laptop:aspect-auto laptop:flex-1">
						{#if expense.receipt_url}
							<a href={expense.receipt_url} target="_blank" rel="noopener" class="size-full" aria-label={format(expenseText.openReceiptPhoto, { name: expense.item_name })}>
								<img src={expense.receipt_url} alt={format(expenseText.receiptOf, { name: expense.item_name })} class="size-full object-cover" />
							</a>
						{:else}
							<span class="flex flex-col items-center gap-2 text-xs text-brand-deep">
								<i class="ti ti-photo text-display" aria-hidden="true"></i>
								{expenseText.noReceiptPhoto}
							</span>
						{/if}
					</div>
				</div>
			</Card>
			<Card class="flex flex-col gap-5">
				<div class="grid gap-5 tablet:grid-cols-2">
					<FigureList
						title={termText.expense}
						figures={[
							{ label: termText.item, value: expense.item_name },
							{ label: termText.price, value: formatRupiah(expense.amount) },
							{ label: expenseText.fundingSource, value: FUND_SOURCES[expense.fund_source] ?? expense.fund_source },
							{ label: termText.ingredient, value: ingredientText(expense) }
						]}
					/>
					<FigureList
						title={termText.recording}
						figures={[
							{ label: termText.branch, value: expense.outlet_name ?? EMPTY_VALUE },
							{ label: termText.day, value: formatDate(expense.business_day) },
							{ label: termText.recordedAt, value: formatDateTime(expense.created_at) },
							{ label: termText.recordedByPerson, value: expense.cashier_username ?? EMPTY_VALUE },
							{ label: expenseText.buyer, value: expense.buyer ?? EMPTY_VALUE }
						]}
					/>
				</div>
				<section class="flex flex-col gap-1 border-t border-slate-100 pt-4 text-xs">
					<h3 class="font-semibold text-slate-600">{termText.note}</h3>
					<p class="whitespace-pre-line {expense.note ? 'text-slate-700' : 'text-slate-500'}">{expense.note ?? termText.noNote}</p>
				</section>
			</Card>
		</div>
	{/snippet}
	{#snippet form(props)}
		<ExpenseForm
			expense={props.record}
			busy={props.busy}
			error={props.error}
			fieldErrors={props.fieldErrors}
			onsave={(body, receipt) => props.onsave({ body, receipt })}
			onclose={props.onclose}
		/>
	{/snippet}
	{#snippet removeNote(expense)}
		{format(expenseText.expenseRemoveNote, { amount: formatRupiah(expense.amount) })}
		{#if expense.session_closed}
			<span class="mt-2 block">{expenseText.closedSessionNote}</span>
		{/if}
		<DepositedDayWarning {warning} />
	{/snippet}
</RecordDetailView>
