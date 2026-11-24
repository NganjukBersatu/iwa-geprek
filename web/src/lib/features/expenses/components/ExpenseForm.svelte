<script lang="ts">
	import { CHOICE_SIZE } from '$lib/api/expenses';
	import { byPage, RemoteChoices } from '$lib/components/form/remote-choices.svelte';
	import { SvelteMap } from 'svelte/reactivity';
	import { controlText } from '$lib/text/controls';
	import { userMessage } from '$lib/api/user-message';
	import { api } from '$lib/api';
	import type { BuyerChoice, Expense, ExpenseReceipt, ExpenseUpdate, IngredientChoice, ReceiptReading, SessionChoice } from '$lib/api/types';
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import DeleteButton from '$lib/components/button/DeleteButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import FormPage from '$lib/components/form/FormPage.svelte';
	import FormSection from '$lib/components/form/FormSection.svelte';
	import BranchField from '$lib/components/form/BranchField.svelte';
	import SelectField from '$lib/components/form/SelectField.svelte';
	import TextArea from '$lib/components/form/TextArea.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import { FieldErrors, focusRefused } from '$lib/components/form/field-errors.svelte';
	import MoneyField from '$lib/components/form/MoneyField.svelte';
	import PhotoField from '$lib/components/form/PhotoField.svelte';
	import PhotoReadButton from '$lib/components/form/PhotoReadButton.svelte';
	import { PAGES, expensePath } from '$lib/nav/pages';
	import { formatDate, todayIso } from '$lib/date/range';
	import { whenChanged } from '$lib/stores/when-changed.svelte';
	import DepositedDayWarning from '../../deposits/components/DepositedDayWarning.svelte';
	import { DayWarning } from '../../deposits/day-warning.svelte';
	import { formatRupiah, rupiahValue } from '$lib/format/currency';
	import { untrack } from 'svelte';
	import SessionPicker from './SessionPicker.svelte';
	import { FUND_SOURCES } from '../../finance/fund-sources';
	import { emptyRow, quantityValue, rowOf, rowsFrom, type ReceiptRow } from '../receipt';
	import { termText } from '$lib/text/terms';
	import { actionText } from '$lib/text/actions';
	import { expenseText } from '$lib/text/expenses';
	import { format } from '$lib/text/format';

	let {
		expense,
		startSession = null,
		fixedOutlet = '',
		busy,
		error,
		fieldErrors = {},
		onsave,
		onrecord,
		onclose
	}: {
		expense: Expense | null;
		startSession?: SessionChoice | null;
		/** Opened from a session: the expense belongs to that session's branch, so the branch is not asked. */
		fixedOutlet?: string;
		busy: boolean;
		error: string;
		/** What the server refused, by field name, shown under the field itself. */
		fieldErrors?: Record<string, string>;
		/** Called when a saved expense is edited; a form that only records new ones leaves it out. */
		onsave?: (body: ExpenseUpdate, receipt: File | null) => void;
		/** A new receipt: every row becomes its own expense sharing the photo. */
		onrecord?: (body: ExpenseReceipt, receipt: File | null, outletId: string) => void;
		onclose: () => void;
	} = $props();

	const NO_SESSION = '';
	const current = untrack(() => expense);
	const trail = [
		{ label: PAGES.expenses.label, href: PAGES.expenses.path },
		...(current ? [{ label: current.item_name, href: expensePath(current.id) }, { label: actionText.edit }] : [{ label: expenseText.recordExpense }])
	];
	const sources = Object.entries(FUND_SOURCES).map(([value, label]) => ({ value, label }));

	let outletId = $state(untrack(() => fixedOutlet));
	// Editing is one row of the same editor, so a saved line can become an ingredient line or a plain one again.
	let rows = $state<ReceiptRow[]>([current ? rowOf(current) : emptyRow()]);
	// Dicari dan dimuat per halaman di server, supaya bahan dan pembeli mana pun terjangkau berapa pun jumlahnya.
	const ingredients = new RemoteChoices<IngredientChoice>(
		byPage(CHOICE_SIZE, (query, page) => (branch ? api.expenses.ingredients(branch, query, page) : Promise.resolve([]))),
		(choice) => choice.id
	);
	const buyers = new RemoteChoices<BuyerChoice>(
		byPage(CHOICE_SIZE, (query, page) => api.expenses.buyers(query, page)),
		(choice) => choice.id
	);
	// Bahan yang sudah dipilih diingat, supaya barisnya tetap bernama walau bahan itu tidak ada di hasil cari terakhir.
	const picked = new SvelteMap<string, IngredientChoice>();
	let source = $state<string>(current?.fund_source ?? 'kas_laci');
	let buyer = $state(current?.buyer ?? '');
	let note = $state(current?.note ?? '');
	let session = $state(untrack(() => startSession?.id ?? NO_SESSION));
	let receipt = $state<File | null>(null);
	let reading = $state<ReceiptReading | null>(null);
	let readError = $state('');
	let target = $state<SessionChoice | null>(untrack(() => startSession));

	/** The first row answers to the field's own name, which is what the server names; the rows after it get a number. */
	const rowField = (field: string, index: number) => (index === 0 ? field : `${field}_${index}`);
	const errors = new FieldErrors(
		() => ({
			outlet_id: termText.branch,
			...Object.fromEntries(rows.flatMap((_, index) => [[rowField('item_name', index), format(expenseText.itemNameWithNumber, { number: rows.length > 1 ? ` ${index + 1}` : '' })], [rowField('amount', index), `Harga${rows.length > 1 ? ` ${index + 1}` : ''}`]])),
			fund_source: expenseText.fundingSource,
			buyer: expenseText.buyer,
			note: termText.note
		}),
		() => fieldErrors
	);

	// A refusal from the server puts the cursor in the first refused box.
	$effect(() => {
		if (Object.keys(fieldErrors).length > 0) void focusRefused();
	});

	// The day the money lands on: the expense's own when editing, else the chosen session's, else today at the branch.
	const warning = new DayWarning();
	whenChanged(
		() => (current ? [{ outlet_id: current.outlet_id, day: current.business_day }] : target ? [{ outlet_id: target.outlet_id, day: target.business_day }] : outletId ? [{ outlet_id: outletId, day: todayIso() }] : []),
		(keys) => void warning.read(keys)
	);

	// A saved expense keeps its branch; a new one follows the branch picked above.
	const branch = $derived(current?.outlet_id ?? outletId);
	const rowsTotal = $derived(rows.reduce((sum, row) => sum + Number(row.amount || 0), 0));
	const matched = $derived(reading?.items.filter((item) => item.ingredient).length ?? 0);
	const buyerOptions = $derived.by(() => {
		const known = buyers.items.map((choice) => ({ value: choice.name, label: choice.outlet_name ? `${choice.name} · ${choice.outlet_name}` : choice.name }));
		// A name typed freely before the list existed stays selectable as it was.
		const kept = buyer && !known.some((option) => option.value === buyer) ? [{ value: buyer, label: buyer }] : [];
		return [...kept, ...known.filter((option, index) => known.findIndex((other) => other.value === option.value) === index)];
	});

	whenChanged(
		() => branch,
		() => ingredients.reset()
	);
	buyers.search('');

	// The saved ingredient may since have gone inactive and left the list; the line still shows it.
	const saved = $derived<IngredientChoice[]>(
		current?.ingredient_id ? [{ id: current.ingredient_id, name: current.ingredient_name ?? current.item_name, unit_id: null, unit_name: current.unit_name }] : []
	);

	/** The suggestions and the saved ingredient may sit outside the loaded list, so they join it, each once. */
	function choicesFor(row: ReceiptRow): IngredientChoice[] {
		const chosen = picked.get(row.ingredientId);
		return [...new Map([...saved, ...(chosen ? [chosen] : []), ...row.suggestions, ...ingredients.items].map((choice) => [choice.id, choice] as const)).values()];
	}

	function ingredientOptions(row: ReceiptRow): { value: string; label: string }[] {
		return choicesFor(row).map((choice) => ({ value: choice.id, label: choice.name }));
	}

	function unitOf(row: ReceiptRow): string {
		return choicesFor(row).find((choice) => choice.id === row.ingredientId)?.unit_name ?? '';
	}

	function pick(row: ReceiptRow, ingredientId: string): void {
		row.ingredientId = ingredientId;
		if (!ingredientId) return void (row.quantity = '');
		const choice = choicesFor(row).find((option) => option.id === ingredientId);
		if (choice) picked.set(choice.id, choice);
		if (choice && !row.name.trim()) row.name = choice.name;
	}
	const printedTotal = $derived(reading?.total ? Math.round(Number(reading.total)) : null);
	const readFrom = $derived([reading?.store, reading?.bought_on ? formatDate(reading.bought_on) : null].filter(Boolean).join(', '));

	async function read(photo: File): Promise<void> {
		readError = '';
		receipt = photo;
		try {
			const found = await api.expenses.readReceipt(photo, branch);
			reading = found;
			rows = rowsFrom(found);
			if (!note.trim() && found.store) note = found.store;
		} catch (failure) {
			reading = null;
			readError = userMessage(failure, expenseText.receiptUnreadable);
		}
	}

	function removeRow(key: number): void {
		rows = rows.filter((row) => row.key !== key);
	}

	function submit(): void {
		const found: Record<string, string> = {};
		rows.forEach((row, index) => {
			if (!row.name.trim()) found[rowField('item_name', index)] = expenseText.itemNameRequired;
			if (rupiahValue(row.amount) <= 0) found[rowField('amount', index)] = expenseText.priceInvalid;
		});
		if (!current && !outletId) found.outlet_id = expenseText.branchRequired;
		if (!errors.check(found)) return;
		if (current) {
			const [row] = rows;
			if (!row) return;
			return onsave?.(
				{
					item_name: row.name.trim(),
					amount: String(rupiahValue(row.amount)),
					// Always sent: null turns the line back into a plain one.
					ingredient_id: row.ingredientId || null,
					quantity: quantityValue(row),
					fund_source: source as ExpenseUpdate['fund_source'],
					buyer: buyer.trim() || null,
					note: note.trim() || null
				},
				receipt
			);
		}
		onrecord?.(
			{
				items: rows.map((row) => ({
					item_name: row.name.trim(),
					amount: String(rupiahValue(row.amount)),
					ingredient_id: row.ingredientId || null,
					quantity: quantityValue(row)
				})),
				fund_source: source as ExpenseReceipt['fund_source'],
				buyer: buyer.trim() || null,
				note: note.trim() || null,
				session_id: session || null
			},
			receipt,
			outletId
		);
	}
</script>

<FormPage title={current ? format(controlText.editName, { name: current.item_name }) : expenseText.recordExpense} description={expenseText.formDescription} stacked {trail} {busy} {onclose}>
	<FormSection icon="shopping-cart" title={expenseText.purchasedItems} description={expenseText.purchasedItemsDescription}>
		{#if !current && !fixedOutlet}
			<BranchField bind:value={outletId} error={errors.get('outlet_id')} />
		{/if}
		<div class="flex flex-col gap-3 rounded-xl border border-slate-200 bg-slate-50 p-3 tablet:p-4">
			{#if !current}
				<div class="flex flex-wrap items-center justify-between gap-2">
					<div class="min-w-0">
						<p class="text-xs text-slate-500">{expenseText.receiptPhotoHint}</p>
					</div>
					<PhotoReadButton label={expenseText.receiptPhoto} disabled={busy} onread={read} />
				</div>
				{#if readError}
					<Banner tone="warning" icon="alert-triangle">{readError}</Banner>
				{:else if reading && reading.items.length === 0 && printedTotal === null}
					<Banner tone="warning" icon="alert-triangle">{expenseText.noItemsRead}</Banner>
				{:else if reading}
					<Banner tone="info" icon="scan">
						{format(expenseText.receiptReadNote, { source: readFrom ? format(expenseText.readFromSource, { source: readFrom }) : '', matched: matched > 0 ? format(expenseText.readMatchedNote, { count: matched }) : '' })}
					</Banner>
				{/if}
			{/if}
			<ul class="flex flex-col gap-3">
				{#each rows as row, index (row.key)}
					<li class="flex flex-col gap-2 rounded-lg border bg-white p-3 {row.ingredientId ? 'border-success-200' : 'border-slate-200'}">
						<div class="grid gap-2 tablet:grid-cols-2">
							<TextField
								label={format(expenseText.itemNameNumber, { number: rows.length > 1 ? index + 1 : '' })}
								bind:value={row.name}
								maxlength={255}
								required
								disabled={!!current?.routine_item_id}
								hint={current?.routine_item_id ? expenseText.routineItemNote : undefined}
								error={errors.get(rowField('item_name', index))}
							/>
							<SelectField label={termText.ingredient} value={row.ingredientId} options={ingredientOptions(row)} empty={expenseText.notIngredient}
								hint={ingredients.problem || undefined}
								onchange={(value) => pick(row, value)}
								onsearch={(text) => ingredients.search(text)}
								onmore={() => ingredients.more()}
								searching={ingredients.searching}
								loadingMore={ingredients.loadingMore}
							/>
						</div>
						{#if !row.ingredientId && row.suggestions.length > 0}
							<div class="flex flex-wrap items-center gap-2">
								<span class="text-xs text-slate-500">{expenseText.maybeIngredient}</span>
								{#each row.suggestions as suggestion (suggestion.id)}
									<Button label={suggestion.name} variant="tertiary" small compact onclick={() => pick(row, suggestion.id)} />
								{/each}
							</div>
						{/if}
						<div class="grid grid-cols-[minmax(0,1fr)_auto] items-end gap-2 {row.ingredientId ? 'tablet:grid-cols-[10rem_minmax(0,1fr)_auto]' : ''}">
							{#if row.ingredientId}
								<TextField label={format(expenseText.quantityWithUnit, { unit: unitOf(row) ? ` (${unitOf(row)})` : '' })} bind:value={row.quantity} inputmode="decimal" hint={expenseText.mayBeEmpty} />
							{/if}
							<MoneyField label={expenseText.priceRupiah} bind:value={row.amount} required error={errors.get(rowField('amount', index))} />
							{#if !current}
								<DeleteButton small disabled={rows.length === 1} onclick={() => removeRow(row.key)} />
							{/if}
						</div>
					</li>
				{/each}
			</ul>
			{#if !current}
				<div class="flex flex-wrap items-center justify-between gap-2">
					<Button label={expenseText.addItem} icon="plus" variant="tertiary" small compact onclick={() => (rows = [...rows, emptyRow()])} />
					<p class="text-sm font-semibold text-slate-800">{format(expenseText.totalWithPeriod, { period: formatRupiah(rowsTotal) })}</p>
				</div>
				{#if printedTotal !== null && printedTotal !== rowsTotal}
					<Banner tone="warning" icon="alert-triangle">{format(expenseText.receiptTotalMismatch, { printed: formatRupiah(printedTotal), rows: formatRupiah(rowsTotal) })}</Banner>
				{/if}
			{/if}
		</div>
	</FormSection>
	<FormSection icon="cash" title={termText.payment} description={expenseText.sourceSectionDescription}>
		<div class="grid gap-2 tablet:grid-cols-2">
			<SelectField label={expenseText.fundingSource} bind:value={source} options={sources} error={errors.get('fund_source')} />
			<SelectField label={expenseText.buyer} bind:value={buyer} options={buyerOptions} empty={expenseText.recordedBy}
				error={errors.get('buyer')}
				hint={buyers.problem || undefined}
				onsearch={(text) => buyers.search(text)}
				onmore={() => buyers.more()}
				searching={buyers.searching}
				loadingMore={buyers.loadingMore}
			/>
		</div>
		{#if !current}
			<SessionPicker bind:value={session} start={startSession} {outletId} onpick={(choice) => (target = choice)} noneLabel="Tanpa sesi (hanya dana lain)" hint={expenseText.sessionRequiredNote} />
		{/if}
	</FormSection>
	<FormSection icon="receipt" title={expenseText.proof} description={expenseText.proofDescription}>
		<TextArea label={termText.note} bind:value={note} rows={2} maxlength={1000} error={errors.get('note')} />
		<PhotoField label={expenseText.receiptPhoto} variant="chooser" current={current?.receipt_url ?? null} alt={format(expenseText.receiptOf, { name: current?.item_name ?? '' })} bind:file={receipt} disabled={busy} />
	</FormSection>

	<DepositedDayWarning {warning} />

	{#if error && errors.count === 0}
		<div class="mt-4"><Banner tone="danger" icon="alert-triangle">{error}</Banner></div>
	{/if}

	{#snippet footer()}
		<SaveButton busy={busy} disabled={warning.checking} onclick={submit} />
		<CancelButton disabled={busy} onclick={onclose} />
	{/snippet}
</FormPage>
