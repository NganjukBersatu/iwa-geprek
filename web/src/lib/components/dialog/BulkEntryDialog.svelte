<script lang="ts">
	import { page } from '$app/state';
	import Banner from '$lib/components/card/Banner.svelte';
	import FormPage from '$lib/components/form/FormPage.svelte';
	import { pageAt } from '$lib/nav/pages';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import { userMessage } from '$lib/api/user-message';
	import { toast } from '$lib/components/feedback/toast.svelte';
	import type { BulkResult } from '$lib/api/types';
	import { dayText, parseDay } from '$lib/date/parse';
	import { summarize } from '$lib/components/table/bulk';
	import { parseNumber } from '$lib/format/number';
	import { untrack } from 'svelte';
	import Button from '../button/Button.svelte';
	import BranchField from '../form/BranchField.svelte';
	import Dropdown from '../form/Dropdown.svelte';
	import type { Field } from '../form/types';
	import Modal from './Modal.svelte';
	import { actionText } from '$lib/text/actions';
	import { controlText } from '$lib/text/controls';
	import { format } from '$lib/text/format';
	import RichText from '$lib/components/text/RichText.svelte';

	let {
		title,
		hint = '',
		columns,
		submit,
		submitLabel = controlText.saveAll,
		initialRows = 5,
		withBranch = false,
		asPage = false,
		onbranch,
		onfinished,
		onclose
	}: {
		title: string;
		hint?: string;
		columns: Field[];
		/** The branch the rows are saved to: the one chosen in the dialog when `withBranch` is set, otherwise an empty text. */
		submit: (rows: Record<string, string | number>[], outletId: string) => Promise<BulkResult>;
		submitLabel?: string;
		initialRows?: number;
		/** Rows that belong to one branch ask which one; the options of the columns follow it through `onbranch`. */
		withBranch?: boolean;
		/** True on a page of its own (a route) instead of a dialog over the list. */
		asPage?: boolean;
		onbranch?: (outletId: string) => void;
		onfinished?: (result: BulkResult) => void;
		onclose: () => void;
	} = $props();

	type Row = { uid: number; values: Record<string, string>; error: string };

	let nextUid = 1;
	const blankRow = (): Row => ({ uid: nextUid++, values: Object.fromEntries(columns.map((column) => [column.key, ''])), error: '' });
	const freshRows = () => Array.from({ length: untrack(() => initialRows) }, blankRow);

	let outletId = $state('');
	let rows = $state<Row[]>(freshRows());
	let sending = $state(false);
	let error = $state('');
	let summary = $state('');

	const parent = $derived(pageAt(page.url.pathname));
	const trail = $derived([...(parent ? [{ label: parent.label, href: parent.path }] : []), { label: title }]);

	const isEmpty = (row: Row) => columns.every((column) => (row.values[column.key] ?? '').trim() === '');
	const filled = $derived(rows.filter((row) => !isEmpty(row)).length);

	$effect(() => {
		if (withBranch) onbranch?.(outletId);
	});

	function addRow(): void {
		rows.push(blankRow());
	}

	function removeRow(uid: number): void {
		rows = rows.filter((row) => row.uid !== uid);
		if (rows.length === 0) addRow();
	}

	function matchOption(column: Field, text: string): string {
		const needle = text.trim().toLowerCase();
		if (!needle) return '';
		const hit = column.options?.find((option) => option.value.toLowerCase() === needle || option.label.toLowerCase() === needle);
		return hit ? hit.value : text.trim();
	}

	/** What a typed or imported cell becomes: an option's value, a day as 01/10/2026, otherwise the trimmed text. */
	function tidy(column: Field, text: string): string {
		if (column.kind === 'select') return matchOption(column, text);
		if (column.kind === 'date') {
			const day = parseDay(text);
			return text.trim() === '' ? '' : day.ok ? dayText(day.iso) : text.trim();
		}
		return text.trim();
	}

	function paste(event: ClipboardEvent, rowIndex: number, columnIndex: number): void {
		const text = event.clipboardData?.getData('text') ?? '';
		if (!/[\t\n]/.test(text.trim())) return;
		event.preventDefault();
		const grid = text.replace(/\r/g, '').replace(/\n+$/, '').split('\n').map((line) => line.split('\t'));
		grid.forEach((cells, offset) => {
			while (rows.length <= rowIndex + offset) addRow();
			const target = rows[rowIndex + offset];
			if (!target) return;
			cells.forEach((cell, shift) => {
				const column = columns[columnIndex + shift];
				if (!column) return;
				target.values[column.key] = tidy(column, cell);
				target.error = '';
			});
		});
	}

	function payload(row: Row): Record<string, string | number> {
		const item: Record<string, string | number> = {};
		for (const column of columns) {
			const value = (row.values[column.key] ?? '').trim();
			if (value === '') continue;
			const day = column.kind === 'date' ? parseDay(value) : null;
			item[column.key] = day?.ok ? day.iso : column.kind === 'number' ? (parseNumber(value) ?? value) : value;
		}
		return item;
	}

	async function save(): Promise<void> {
		error = '';
		summary = '';
		if (withBranch && !outletId) {
			error = controlText.branchRequired;
			return;
		}
		const sent = rows.filter((row) => !isEmpty(row));
		if (sent.length === 0) {
			error = controlText.noRowsFilled;
			return;
		}
		let incomplete = false;
		for (const row of sent) {
			const missing = columns.filter((column) => column.required && (row.values[column.key] ?? '').trim() === '');
			const unreadable = columns.map((column) => (column.kind === 'date' && (row.values[column.key] ?? '').trim() !== '' ? parseDay(row.values[column.key] ?? '') : null)).find((day) => day && !day.ok);
			row.error = missing.length ? format(controlText.fillColumns, { columns: missing.map((column) => column.label).join(', ') }) : unreadable && !unreadable.ok ? unreadable.message : '';
			if (row.error) incomplete = true;
		}
		if (incomplete) {
			error = controlText.rowsIncomplete;
			return;
		}

		sending = true;
		try {
			const result = await submit(sent.map(payload), outletId);
			const failed = new Set<number>();
			for (const outcome of result.results) {
				const row = sent[outcome.row - 1];
				if (row && !outcome.ok) {
					row.error = outcome.error ?? controlText.failed;
					failed.add(row.uid);
				}
			}
			const remaining = rows.filter((row) => failed.has(row.uid));
			rows = remaining.length ? remaining : freshRows();
			summary = summarize(result, 'disimpan');
			onfinished?.(result);
			if (result.failed === 0) {
				toast.show(summary);
				onclose();
			}
		} catch (cause) {
			error = userMessage(cause, controlText.saveFailed);
		} finally {
			sending = false;
		}
	}
</script>

{#snippet content()}
	{#if withBranch}
		<div class="mb-3"><BranchField bind:value={outletId} /></div>
	{/if}
	<p class="text-xs leading-5 text-slate-500">
		<RichText template={controlText.bulkEntryPasteHint} values={{ label: controlText.pasteFromSheets, hint: hint }} />
	</p>

	<div class="mt-3 overflow-x-auto rounded-lg border border-slate-200">
		<table class="w-full min-w-xl text-sm">
			<thead class="bg-slate-50 text-left text-xs text-slate-500">
				<tr>
					<th class="w-8 px-2 py-2 text-center font-medium">#</th>
					{#each columns as column (column.key)}
						<th class="px-1 py-2 font-medium">{column.label}{#if column.required}<span class="text-danger-500"> *</span>{/if}</th>
					{/each}
					<th class="w-8"><span class="sr-only">{controlText.removeRow}</span></th>
				</tr>
			</thead>
			<tbody class="divide-y divide-slate-100">
				{#each rows as row, rowIndex (row.uid)}
					<tr class={row.error ? 'bg-danger-50' : ''}>
						<td class="px-2 py-1 text-center text-xs text-slate-500">{rowIndex + 1}</td>
						{#each columns as column, columnIndex (column.key)}
							<td class="px-1 py-1">
								{#if column.kind === 'select'}
									<Dropdown bind:value={row.values[column.key]} options={column.options ?? []} empty="—" aria-label={format(controlText.columnRow, { column: column.label, row: rowIndex + 1 })} size="sm" class="w-full" />
								{:else}
									<input
										bind:value={row.values[column.key]}
										inputmode={column.kind === 'number' ? 'decimal' : 'text'}
										placeholder={column.placeholder ?? (column.kind === 'date' ? 'dd/mm/yyyy' : '')}
										onblur={column.kind === 'date' ? () => (row.values[column.key] = tidy(column, row.values[column.key] ?? '')) : undefined}
										aria-label={format(controlText.columnRow, { column: column.label, row: rowIndex + 1 })}
										onpaste={(event) => paste(event, rowIndex, columnIndex)}
										class="w-full rounded-lg border border-slate-200 px-2 py-1.5 text-sm focus:border-brand focus:outline-none {column.kind === 'number' ? 'text-right' : ''}"
									/>
								{/if}
							</td>
						{/each}
						<td class="px-1 py-1 text-center">
							<button type="button" onclick={() => removeRow(row.uid)} aria-label={format(controlText.removeRowNumber, { row: rowIndex + 1 })} class="rounded-lg p-1 text-slate-500 hover:bg-slate-100 hover:text-danger-500">
								<i class="ti ti-x" aria-hidden="true"></i>
							</button>
						</td>
					</tr>
					{#if row.error}
						<tr class="bg-danger-50"><td></td><td colspan={columns.length + 1} class="px-2 pb-1.5 text-xs text-danger-700">{row.error}</td></tr>
					{/if}
				{/each}
			</tbody>
		</table>
	</div>

	<div class="mt-3 flex items-center justify-between gap-2">
		<Button label={controlText.addRow} icon="plus" onclick={addRow} />
		<p class="text-xs text-slate-500">{format(controlText.rowsFilled, { count: filled })}</p>
	</div>

	{#if error}
		<div class="mt-3"><Banner tone="danger" icon="alert-triangle">{error}</Banner></div>
	{/if}
	{#if summary}
		<div class="mt-3"><Banner tone="success" icon="circle-check">{summary}</Banner></div>
	{/if}
{/snippet}

{#snippet actions()}
	<SaveButton label={submitLabel} busy={sending} disabled={filled === 0} onclick={() => void save()} />
	<Button label={actionText.close} disabled={sending} onclick={onclose} />
{/snippet}

{#if asPage}
	<FormPage wide {title} description={controlText.bulkEntryHint} {trail} busy={sending} {onclose} footer={actions}>
		{@render content()}
	</FormPage>
{:else}
	<Modal open {title} size="lg" busy={sending} {onclose}>
		{@render content()}

		{#snippet footer()}
			<Button label={actionText.close} disabled={sending} onclick={onclose} />
			<SaveButton label={submitLabel} busy={sending} disabled={filled === 0} onclick={() => void save()} />
		{/snippet}
	</Modal>
{/if}
