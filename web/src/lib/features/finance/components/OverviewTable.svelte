<script lang="ts">
	import { dynamicStyle } from '$lib/motion/actions';
	import type { DailyRow, DailyTotals } from '$lib/api/types';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import MatrixTable, { type MatrixColumn, type MatrixGroup } from '$lib/components/table/MatrixTable.svelte';
	import PickBox from '$lib/components/table/PickBox.svelte';
	import { dayLabel, formatDayMonth } from '$lib/date/range';
	import { formatAmount, formatPercentPlain } from '$lib/format/currency';
	import type { DepositsState } from '../../deposits/deposits.svelte';
	import { STATUS_LABEL, STATUS_TONE } from '../../deposits/format';
	import { termText } from '$lib/text/terms';
	import { financeText } from '$lib/text/finance';
	import { format } from '$lib/text/format';

	let { title, rows, total, deposits = null }: { title: string; rows: DailyRow[]; total: DailyTotals; deposits?: DepositsState | null } = $props();

	type Part = 'cash' | 'nonCash' | 'total' | 'percent';
	type Field = keyof DailyTotals;
	type Group = { id: 'income' | 'expense' | 'profit'; label: string; head: string; fields: Partial<Record<Part, Field>> };
	/** The TOTAL line on top, then one line per day. */
	type Line = { kind: 'total'; totals: DailyTotals } | { kind: 'day'; totals: DailyRow };

	const partLabels: Record<Part, string> = { cash: financeText.cash, nonCash: termText.nonCash, total: termText.total, percent: '%' };
	const groups: Group[] = [
		{ id: 'income', label: termText.income, head: 'bg-brand text-brand-on', fields: { cash: 'cash_income', nonCash: 'non_cash_income', total: 'income_total' } },
		{
			id: 'expense',
			label: termText.expense,
			head: 'bg-brand-accent text-brand-ink',
			fields: { cash: 'cash_expense', nonCash: 'non_cash_expense', total: 'expense_total', percent: 'expense_percent' }
		},
		{
			id: 'profit',
			label: termText.profit,
			head: 'bg-brand-ink text-brand-on',
			fields: { cash: 'cash_profit', nonCash: 'non_cash_profit', total: 'profit_total', percent: 'profit_percent' }
		}
	];
	const partsOf = (group: Group) => Object.keys(group.fields) as Part[];
	const SETORAN = { status: 'setoran:status', paid: 'setoran:paid', left: 'setoran:left' } as const;

	function value(source: DailyTotals, group: Group, part: Part): string {
		return source[group.fields[part]!];
	}

	function text(source: DailyTotals, group: Group, part: Part): string {
		return part === 'percent' ? formatPercentPlain(value(source, group, part)) : formatAmount(value(source, group, part));
	}

	function ink(source: DailyTotals, group: Group, part: Part, empty: boolean): string {
		const profit = group.id === 'profit';
		if (profit && (part === 'total' || part === 'percent') && Number(source.profit_total) < 0) return 'text-danger-700';
		if (empty) return '';
		if (part === 'percent') return profit ? 'text-success-700' : 'text-danger-700';
		return profit && part === 'total' ? 'text-success-700' : '';
	}

	const isEmpty = (line: Line) => line.kind === 'day' && Number(line.totals.income_total) === 0 && Number(line.totals.expense_total) === 0;

	/** The Setoran group is only drawn when it is switched on and the branch's deposits have arrived. */
	const show = $derived(!!deposits && deposits.columns && deposits.data !== null);
	const picking = $derived(deposits?.selection.enabled ?? false);
	const stripe = (status: string | undefined) =>
		status === 'belum' ? 'shadow-[inset_4px_0_0_0_var(--color-danger-500)]' : status === 'sebagian' ? 'shadow-[inset_4px_0_0_0_var(--color-warning-500)]' : '';
	const depositOf = (line: Line) => (show && line.kind === 'day' ? deposits?.dayOf(line.totals.date) : undefined);

	const lines = $derived<Line[]>([{ kind: 'total', totals: total }, ...rows.map((row) => ({ kind: 'day' as const, totals: row }))]);
	const matrixGroups = $derived<MatrixGroup[]>([
		...groups.map((group) => ({ key: group.id, label: group.label, span: partsOf(group).length, head: group.head })),
		...(show ? [{ key: 'setoran', label: financeText.deposit, span: 3, head: 'bg-brand-muted text-brand-on', pin: 'sticky right-0 z-20 border-l border-white/20' }] : [])
	]);
	// The three Setoran columns are pinned to the right edge, each at the summed width of those after it.
	const columns = $derived<MatrixColumn[]>([
		...groups.flatMap((group) => partsOf(group).map((part) => ({ key: `${group.id}:${part}`, label: partLabels[part], strong: part === 'total' }))),
		...(show
			? [
					{ key: SETORAN.status, label: termText.status, pin: 'right-55 w-28 min-w-28 border-l border-slate-200 text-left' },
					{ key: SETORAN.paid, label: financeText.deposited, pin: 'right-25 w-30 min-w-30' },
					{ key: SETORAN.left, label: termText.remaining, pin: 'right-0 w-25 min-w-25', strong: true }
				]
			: [])
	]);

	function partOf(key: string): { group: Group; part: Part } | null {
		const [id, part] = key.split(':');
		const group = groups.find((entry) => entry.id === id);
		return group ? { group, part: part as Part } : null;
	}
</script>

<Card flush>
	<CardHeader divided title={format(financeText.summaryOf, { title: title })} />
	<MatrixTable
		leadLabel="Tanggal"
		{columns}
		groups={matrixGroups}
		rows={lines}
		rowKey={(line) => (line.kind === 'total' ? 'total' : line.totals.date)}
		rowClass={(line) => (line.kind === 'total' ? 'bg-slate-100 font-semibold text-slate-800' : `bg-white ${isEmpty(line) ? 'text-slate-300' : 'text-slate-700'}`)}
		leadClass={(line) => stripe(depositOf(line)?.status)}
		onrowclick={(line) => (depositOf(line) && deposits && line.kind === 'day' ? () => (deposits.detail = { kind: 'day', id: line.totals.date }) : undefined)}
		minWidth="min-w-225"
	>
		{#snippet lead(line)}
			<span class="inline-flex items-center gap-2">
				{#if picking && deposits}
					{#if line.kind === 'total'}
						<PickBox
							label={financeText.selectAllHeldDays}
							checked={deposits.selection.allIn(deposits.openDays)}
							disabled={deposits.openDays.length === 0}
							onchange={() => deposits.selection.setAll(deposits.openDays, !deposits.selection.allIn(deposits.openDays))}
						/>
					{:else if Number(depositOf(line)?.left ?? 0) > 0}
						<PickBox label={format(financeText.chooseDay, { date: formatDayMonth(line.totals.date) })} checked={deposits.selection.has(line.totals.date)} onchange={() => deposits.selection.toggle(line.totals.date)} />
					{:else}
						<span class="size-4 shrink-0"></span>
					{/if}
				{/if}
				{#if line.kind === 'total'}
					{financeText.total}
				{:else}
					{@const label = dayLabel(line.totals.date)}
					<span><span class={label.sunday ? 'text-danger-500' : ''}>{label.weekday}</span> {label.day}</span>
				{/if}
			</span>
		{/snippet}
		{#snippet cell(line, column)}
			{@const found = partOf(column.key)}
			{@const deposit = depositOf(line)}
			{#if found}
				{@const empty = isEmpty(line)}
				<span class="{found.part === 'total' && !empty && line.kind === 'day' ? 'text-slate-800' : ''} {ink(line.totals, found.group, found.part, empty)}">
					{text(line.totals, found.group, found.part)}
				</span>
			{:else if line.kind === 'total' && deposits?.data}
				{#if column.key === SETORAN.paid}{formatAmount(deposits.data.summary.paid_total)}{/if}
				{#if column.key === SETORAN.left}<span class={Number(deposits.data.summary.held) > 0 ? 'text-danger-700' : ''}>{formatAmount(deposits.data.summary.held)}</span>{/if}
			{:else if deposit}
				{#if column.key === SETORAN.status}
					<Badge tone={STATUS_TONE[deposit.status]}>{STATUS_LABEL[deposit.status]}</Badge>
				{:else if column.key === SETORAN.paid}
					{@const percent = Math.min(100, Math.round((Number(deposit.paid) / (Number(deposit.due) || 1)) * 100))}
					<span class="text-slate-700">{Number(deposit.paid) > 0 ? formatAmount(deposit.paid) : '0'}</span>
					<span class="mt-1 block h-1 overflow-hidden rounded-full bg-slate-100" aria-hidden="true">
						<span class="block h-full {deposit.status === 'sebagian' ? 'bg-warning-500' : 'bg-success-500'}" use:dynamicStyle={{ width: `${percent}%` }}></span>
					</span>
				{:else}
					<span class={Number(deposit.left) > 0 ? 'text-danger-700' : 'text-slate-500'}>{formatAmount(deposit.left)}</span>
				{/if}
			{/if}
		{/snippet}
	</MatrixTable>
</Card>
