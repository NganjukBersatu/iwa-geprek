<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import BulkEntryDialog from '$lib/components/dialog/BulkEntryDialog.svelte';
	import ConfirmDialog from '$lib/components/dialog/ConfirmDialog.svelte';
	import BranchField from '$lib/components/form/BranchField.svelte';
	import type { Field } from '$lib/components/form/types';
	import TextField from '$lib/components/form/TextField.svelte';
	import { pageOf } from '$lib/components/pager/page-of';
	import Pager from '$lib/components/pager/Pager.svelte';
	import { withBranchColumn } from '$lib/components/table/branch-column';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { formatDate, formatRange, shiftDays, todayIso } from '$lib/date/range';
	import { frame } from '$lib/motion/spotlight';
	import { ingredientCountPath, PAGES } from '$lib/nav/pages';
	import CloseGuide from './CloseGuide.svelte';
	import CountDifference from './CountDifference.svelte';
	import RequestProgress from '../../ingredient-count-requests/components/RequestProgress.svelte';
	import PendingRequestsCard from '../../ingredient-count-requests/components/PendingRequestsCard.svelte';
	import { IngredientCountRequestsState } from '../../ingredient-count-requests/ingredient-count-requests.svelte';
	import { EMPTY_VALUE, formatNumber } from '$lib/format/currency';
	import type { IngredientCountsState } from '../ingredient-counts.svelte';
	import { HISTORY_TONES, historyColumns, historyPeriod, movementColumns, sheetColumns, type CountHistoryRow } from '../columns';
	import { detailColumns, lineStatus, STATUS_LABELS, STATUS_TONES } from '../../ingredient-count-detail/columns';
	import { termText } from '$lib/text/terms';
	import { ingredientCountText } from '$lib/text/ingredient-counts';
	import { format } from '$lib/text/format';

	let { counts }: { counts: IngredientCountsState } = $props();

	let sheet = $state<HTMLElement>();
	let sheetCard = $state<HTMLElement>();
	// Rentang yang belum berakhir berarti periode masih berjalan; tombolnya dibedakan supaya tidak tertutup lebih awal tanpa sadar.
	const early = $derived(counts.query.range !== null && counts.query.range.to >= todayIso());

	/** Membawa pengguna ke kolom jumlah fisik: semua isian yang terlihat disorot sesaat dan kursor masuk ke isian pertama. */
	function pointToCounted(): void {
		const cells = [...(sheet?.querySelectorAll<HTMLElement>('[data-counted]') ?? [])].filter((cell) => cell.offsetParent !== null);
		const first = cells.at(0);
		if (!first) return;
		frame(first, 'center');
		for (const cell of cells.slice(1)) frame(cell, null);
		first.querySelector('input')?.focus({ preventScroll: true });
	}

	const requests = new IngredientCountRequestsState();

	const shownHistoryColumns = $derived(withBranchColumn(historyColumns, counts.filters.allBranches));
	const rows = $derived(counts.sheet?.rows ?? []);
	let page = $state(1);
	const shown = $derived(pageOf(rows, page));
	const untouched = $derived(Math.max(0, rows.length - counts.filled));
	const missing = $derived(counts.missingOpening);
	const settled = $derived(counts.settled);
	const columns = $derived(settled ? detailColumns : counts.canCount ? sheetColumns : movementColumns);
	const pending = $derived(counts.request?.status === 'pending' ? counts.request : null);
	const rangeLabel = $derived(counts.query.range ? formatRange(counts.query.range) : '');

	const openingColumns = $derived<Field[]>([
		{ key: 'ingredient_id', label: termText.ingredient, kind: 'select', required: true, options: counts.ingredients.map((item) => ({ value: item.id, label: `${item.name} (${item.unit})` })) },
		{ key: 'opening', label: ingredientCountText.openingStockLower, kind: 'number', required: true },
		{ key: 'from_date', label: ingredientCountText.startDate, kind: 'date', required: true }
	]);

	/** Leaving the screen saves what was typed in the last moment. */
	onMount(() => () => void counts.flush());

	/** A closed period opens its own page; the running one opens the worksheet, since nothing in it is closed yet. */
	function open(row: CountHistoryRow): void {
		if (row.id) {
			void goto(ingredientCountPath(row.id, row.part_start));
			return;
		}
		void counts.openRunning(row).then(() => sheetCard?.scrollIntoView({ block: 'start' }));
	}
</script>

{#if counts.actionError && !counts.closing && !counts.requesting}
	<Banner tone="danger" icon="alert-triangle">{counts.actionError}</Banner>
{/if}

{#if counts.canCount}
	<PendingRequestsCard {requests} />
{/if}

<div bind:this={sheetCard} class="scroll-mt-4" aria-hidden="true"></div>

{#if !counts.query.range}
	<Notice text={ingredientCountText.choosePeriod} />
{:else if !counts.branch}
	<Card flush>
		<CardHeader divided title={ingredientCountText.sheetTitle} description={ingredientCountText.chooseBranch} />
		<div class="px-4 py-4 tablet:max-w-sm tablet:px-5"><BranchField bind:value={counts.sheetBranch} onchange={() => counts.changeSheetBranch()} /></div>
	</Card>
{:else if counts.sheet}
	{@const opening = counts.openingStatus}
	{#if !settled && opening && opening.total > 0 && opening.filled < opening.total}
		<Banner tone="warning" icon="alert-triangle" title={format(ingredientCountText.missingOpeningTitle, { filled: formatNumber(opening.filled, 0), total: formatNumber(opening.total, 0) })}>
			{format(ingredientCountText.missingOpeningBody, { start: formatDate(opening.start) })}
			{#snippet action()}
				{#if counts.canCount}
					<Button label={ingredientCountText.fillOpening} icon="table-plus" variant="primary" compact onclick={() => counts.openOpening()} />
				{/if}
			{/snippet}
		</Banner>
	{/if}
	<Card flush>
		<CardHeader
			divided
			title={settled ? format(ingredientCountText.settledTitle, { range: rangeLabel }) : ingredientCountText.sheetTitle}
			description={settled ? ingredientCountText.settledDescription : counts.canCount ? ingredientCountText.sheetDescriptionCounter : ingredientCountText.requesterDescription}
		>
			{#snippet actions()}
				{#if counts.canCount}
					<Button label={ingredientCountText.guide} icon="help-circle" compact onclick={() => counts.showGuide(true)} />
				{/if}
			{/snippet}
		</CardHeader>

		{#if counts.filters.allBranches}
			<div class="px-4 pt-4 tablet:max-w-sm tablet:px-5"><BranchField bind:value={counts.sheetBranch} onchange={() => counts.changeSheetBranch()} /></div>
		{/if}
		{#if rows.length === 0}
			<Notice text={controlText.noIngredients} />
		{:else}
			<div bind:this={sheet} class="contents">
				<DataTable sort={counts.sheetSort} {columns} rows={shown.rows} rowKey={(row) => row.ingredient_id} loading={counts.loading} trailing={settled ? 'status' : counts.canCount ? 'selisih' : 'akhir'}>
					{#snippet cell(row, column)}
						{#if settled && column.key === 'status'}
							<Badge tone={STATUS_TONES[lineStatus(row)]}>{STATUS_LABELS[lineStatus(row)]}</Badge>
						{:else if settled}
							{column.value(row)}
						{:else if column.key === 'real'}
							<div class="ml-auto w-24 rounded-lg" data-counted>
								<TextField
									compact
									label={format(controlText.countedOf, { name: row.name })}
									inputmode="decimal"
									placeholder={EMPTY_VALUE}
									bind:value={() => counts.counted[row.ingredient_id] ?? '', (typed) => counts.type(row.ingredient_id, typed)}
								/>
							</div>
						{:else if column.key === 'selisih'}
							<CountDifference difference={counts.difference(row.ingredient_id, row.closing_stock)} closing={row.closing_stock} />
						{:else if column.key === 'bahan' && missing.has(row.ingredient_id)}
							<span class="flex flex-col">
								<span>{column.value(row)}</span>
								<span class="flex items-center gap-1 text-xs font-semibold text-warning-700"><i class="ti ti-alert-triangle" aria-hidden="true"></i>{ingredientCountText.missingOpeningTag}</span>
							</span>
						{:else}
							{column.value(row)}
						{/if}
					{/snippet}
				</DataTable>
			</div>
			<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
				<Pager page={shown.page} total={rows.length} unit="bahan" disabled={counts.loading} onchange={(next) => (page = next)} />
			</div>
			{#if !settled && counts.canRequest}
				<div class="flex flex-wrap items-center gap-3 border-t border-slate-100 px-4 py-4 tablet:px-5">
					{#if counts.request}
						<div class="flex w-full flex-col gap-2">
							<span class="text-sm font-medium text-slate-800">{format(ingredientCountText.lastRequest, { from: formatDate(counts.request.close_start), to: formatDate(counts.request.close_end) })}</span>
							<RequestProgress request={counts.request} />
						</div>
					{/if}
					{#if !pending}
						<Button label={counts.query.range ? format(ingredientCountText.requestCloseRange, { range: rangeLabel }) : ingredientCountText.requestClose} icon="send" variant="primary" disabled={counts.busy} onclick={() => counts.askRequest()} />
					{/if}
				</div>
			{/if}
			{#if !settled && counts.canCount}
				<div class="flex flex-col gap-3 border-t border-slate-100 px-4 py-4 tablet:px-5">
					<div class="tablet:max-w-md"><TextField label={termText.note} bind:value={counts.note} maxlength={255} placeholder={ingredientCountText.noteExample} /></div>
					{#if counts.problem}<p class="rounded-lg border border-danger-200 bg-danger-50 px-3 py-2 text-xs text-danger-700" role="alert">{counts.problem}</p>{/if}
					<div class="flex flex-wrap items-center gap-3">
						<Button
							label={counts.query.range ? format(early ? ingredientCountText.closeEarlyRange : ingredientCountText.closeRange, { range: rangeLabel }) : ingredientCountText.closePeriod}
							icon="lock"
							variant={early ? 'secondary' : 'primary'}
							disabled={counts.busy}
							onclick={() => {
								if (!counts.askClose()) pointToCounted();
							}}
						/>
						<span class="text-xs text-slate-500">{format(ingredientCountText.ingredientsCount, { count: formatNumber(counts.filled, 0) })}</span>
						{#if early}
							<span class="text-xs text-slate-500">{ingredientCountText.stillRunningNote}</span>
						{/if}
						{#if counts.openSessions !== null && counts.openSessions > 0}
							<span class="flex items-center gap-1 text-xs font-semibold text-warning-700" role="status">
								<i class="ti ti-alert-triangle" aria-hidden="true"></i>{format(ingredientCountText.openSessionsWarning, { count: formatNumber(counts.openSessions, 0) })}
								<a class="font-semibold text-brand underline" href={PAGES.sessionHistory.path}>{ingredientCountText.openSessionHistory}</a>
							</span>
						{/if}
						<span class="text-xs {counts.draftProblem ? 'text-danger-700' : 'text-slate-500'}" role={counts.draftProblem ? 'alert' : 'status'}>{counts.draftProblem || (counts.draftSavedAt ? format(ingredientCountText.draftSavedAt, { time: counts.draftSavedAt }) : ingredientCountText.draftAuto)}</span>
					</div>
				</div>
			{/if}
		{/if}
	</Card>
{/if}

<Card flush>
	<CardHeader divided title={ingredientCountText.historyTitle} description={ingredientCountText.historyDescriptionByPeriod} />
	{#if counts.historyRows.length === 0}
		<Notice text={ingredientCountText.noPeriods} />
	{:else}
		<DataTable sort={counts.historySort} columns={shownHistoryColumns} rows={counts.historyRows} rowKey={(row) => row.key} loading={counts.loading} trailing="ditutup" onopen={open}>
			{#snippet first(row)}
				<span class="block">{historyPeriod(row)}</span>
				{#if row.state === 'running'}
					<span class="block text-xs font-normal text-slate-500">{format(ingredientCountText.notClosedDays, { days: formatNumber(row.days ?? 0, 0) })}</span>
				{:else if row.state === 'to_close'}
					<span class="block text-xs font-normal text-slate-500">{ingredientCountText.toCloseNote}</span>
				{:else if row.state === 'opening'}
					<span class="block text-xs font-normal text-slate-500">{ingredientCountText.openingNote}</span>
				{:else if row.note}
					<span class="block max-w-xs truncate text-xs font-normal text-slate-500">{row.note}</span>
				{/if}
			{/snippet}
			{#snippet cell(row, column)}
				{#if column.key === 'status'}
					<Badge tone={row.requested ? 'warning' : HISTORY_TONES[row.state]}>{column.value(row)}</Badge>
				{:else if column.key === 'sumber' && row.source}
					<Badge tone="neutral">{column.value(row)}</Badge>
				{:else}
					{column.value(row)}
				{/if}
			{/snippet}
		</DataTable>
	{/if}
</Card>

<ConfirmDialog
	open={counts.closing}
	title={counts.query.range ? format(ingredientCountText.closePeriodNamed, { range: rangeLabel }) : ingredientCountText.closePeriod}
	confirmLabel={ingredientCountText.confirmClose}
	busy={counts.busy}
	error={counts.actionError}
	onconfirm={() => void counts.close()}
	oncancel={() => counts.closeDialogs()}
>
	<p>{format(ingredientCountText.closePeriodNote, { count: counts.filled })}</p>
	<div class="mt-3">
		<Banner tone="warning" icon="alert-triangle" title={ingredientCountText.newPeriodFromZero}>
			<ul class="mt-1 list-disc space-y-0.5 pl-4">
				<li>{format(ingredientCountText.closePeriodResetNote, { total: formatNumber(rows.length, 0), untouched: formatNumber(untouched, 0) })}</li>
				<li>{ingredientCountText.menuStillOrderable}</li>
				<li>{ingredientCountText.resaleNotZeroed}</li>
				<li>{ingredientCountText.dataKept}</li>
				{#if missing.size > 0}
					<li class="font-semibold">{format(ingredientCountText.missingOpeningWarning, { count: formatNumber(missing.size, 0) })}</li>
				{/if}
			</ul>
		</Banner>
	</div>
</ConfirmDialog>

<ConfirmDialog
	open={counts.requesting}
	title={counts.query.range ? format(ingredientCountText.requestCloseRange, { range: rangeLabel }) : ingredientCountText.requestClose}
	confirmLabel={ingredientCountText.requestConfirm}
	busy={counts.busy}
	error={counts.actionError}
	onconfirm={() => void counts.submitRequest()}
	oncancel={() => counts.closeDialogs()}
>
	<p>{format(ingredientCountText.requestIntro, { total: formatNumber(rows.length, 0) })}</p>
	<div class="mt-3"><TextField label={ingredientCountText.requestNoteLabel} bind:value={counts.requestNote} maxlength={255} placeholder={ingredientCountText.requestNotePlaceholder} /></div>
</ConfirmDialog>

{#if counts.openingOpen}
	<BulkEntryDialog
		title={ingredientCountText.openingBulkTitle}
		hint={ingredientCountText.openingBulkHint}
		columns={openingColumns}
		withBranch
		onbranch={(outletId) => void counts.loadIngredients(outletId)}
		submit={(rows, outletId) => counts.createOpening(rows, outletId)}
		submitLabel="Simpan stok awal"
		onclose={() => counts.closeDialogs()}
	/>
{/if}

{#if counts.canCount && counts.query.range && counts.sheet}
	<CloseGuide open={counts.guideOpen} start={counts.query.range.from} end={counts.query.range.to} nextStart={shiftDays(counts.query.range.to, 1)} onclose={() => counts.showGuide(false)} />
{/if}
