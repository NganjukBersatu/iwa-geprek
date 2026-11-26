<script lang="ts">
	import { goto } from '$app/navigation';
	import { untrack } from 'svelte';
	import { api } from '$lib/api';
	import type { Batch, BatchCopyResult, BatchInput, BatchRun } from '$lib/api/types';
	import { userMessage } from '$lib/api/user-message';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import FigureList from '$lib/components/card/FigureList.svelte';
	import { toast } from '$lib/components/feedback/toast.svelte';
	import SkeletonList from '$lib/components/skeleton/SkeletonList.svelte';
	import RichText from '$lib/components/text/RichText.svelte';
	import { formatDate, shiftDays, todayIso } from '$lib/date/range';
	import { EMPTY_VALUE } from '$lib/format/currency';
	import { formatClockRange, formatTime } from '$lib/format/datetime';
	import { PAGES, batchRunPath, tasksTabPath } from '$lib/nav/pages';
	import { branchList } from '$lib/stores/branch';
	import { actionText } from '$lib/text/actions';
	import { batchText } from '$lib/text/batches';
	import { format } from '$lib/text/format';
	import { recordText } from '$lib/text/record-detail';
	import { termText } from '$lib/text/terms';
	import RecordDetailView from '../../record-detail/components/RecordDetailView.svelte';
	import { RecordDetailState } from '../../record-detail/record-detail.svelte';
	import { BATCH_TABLES } from '../batches.svelte';
	import { fillLabel, ITEM_KINDS, repeatLabel, TARGET_USER, type BatchKind } from '../constants';
	import BatchCopyDialog from './BatchCopyDialog.svelte';
	import BatchForm from './BatchForm.svelte';
	import ShiftCodeBadge from '$lib/components/card/ShiftCodeBadge.svelte';

	let { id }: { id: string } = $props();

	/** Recent fillings shown on the task; older ones are in the history tab. */
	const RECENT_RUNS = 5;
	// The history without dates holds only this month, so the task asks for a longer range.
	const RECENT_DAYS = 90;

	const detail = new RecordDetailState<Batch, BatchInput, null>(untrack(() => id), {
		load: (batchId) => api.batches.detail(batchId),
		update: (batch, body) => api.batches.update(batch.id, body),
		remove: (batch) => api.batches.remove(batch.id),
		name: (batch) => batch.name,
		text: recordText(batchText.taskNoun, PAGES.tasks.label)
	});

	let runs = $state<BatchRun[]>([]);
	let runsLoading = $state(true);
	let runsError = $state('');
	let copying = $state(false);
	let copyBusy = $state(false);
	let copyError = $state('');
	let copyResult = $state<BatchCopyResult | null>(null);
	let outlets = $state<{ id: string; name: string }[]>([]);

	const textOf = (batch: Batch) => batchText.kinds[batch.kind as BatchKind];

	async function loadRuns(): Promise<void> {
		runsLoading = true;
		runsError = '';
		try {
			const today = todayIso();
			runs = (await api.batches.runs({ batch_id: id, date_from: shiftDays(today, -RECENT_DAYS), date_to: today, page: 1, size: RECENT_RUNS })).items;
		} catch (failure) {
			runsError = userMessage(failure, batchText.recentRunsFailed);
		} finally {
			runsLoading = false;
		}
	}

	$effect(() => {
		void loadRuns();
	});

	/** Turns the task on or off in the app without opening the form; the rest of the task is sent as it is. */
	async function setActive(batch: Batch, active: boolean): Promise<void> {
		const { repeat_unit: unit, starts_on: start } = batch;
		if (!unit || !start) {
			toast.show(batchText.legacyToggle);
			return;
		}
		const body: BatchInput = {
			kind: batch.kind,
			fill_mode: batch.fill_mode,
			target: batch.target,
			shift_code_ids: batch.shift_codes.map((code) => code.id),
			user_ids: batch.user.map((person) => person.id),
			name: batch.name,
			start_clock: batch.start_clock,
			end_clock: batch.end_clock,
			repeat_unit: unit,
			repeat_every: batch.repeat_every,
			starts_on: start,
			is_active: active,
			items: batch.items.map((item) => ({ id: item.id, label: item.label, kind: item.kind, required: item.required }))
		};
		const done = await detail.change(() => api.batches.update(batch.id, body), format(batchText.toggleFailed, { noun: textOf(batch).noun }));
		if (done) toast.show(format(active ? batchText.activated : batchText.deactivated, { name: batch.name }));
	}

	async function openCopy(): Promise<void> {
		copyError = '';
		copyResult = null;
		copying = true;
		try {
			outlets = await branchList();
		} catch (failure) {
			copyError = userMessage(failure, batchText.copyFailed);
		}
	}

	async function copy(batch: Batch, outletIds: string[]): Promise<void> {
		copyBusy = true;
		copyError = '';
		try {
			copyResult = await api.batches.copy(batch.id, outletIds);
		} catch (failure) {
			copyError = userMessage(failure, format(batchText.copyFailed, { noun: textOf(batch).noun }));
		} finally {
			copyBusy = false;
		}
	}

	const rowsOf = (batch: Batch) => {
		const named = batch.target === TARGET_USER;
		const entries: [string, string | null][] = [
			[batchText.branch, batch.outlet_name],
			[batchText.columnHours, formatClockRange(batch.start_clock, batch.end_clock)],
			[batchText.columnRepeat, repeatLabel(batch)],
			[batchText.startsOnDetail, batch.starts_on ? formatDate(batch.starts_on) : null],
			[batchText.columnRecipient, named && batch.user.length > 0 ? batch.user.map((person) => person.name).join(', ') : null],
			[batchText.columnFiller, batch.kind === 'routine' ? fillLabel(batch.fill_mode) : null]
		];
		return entries.flatMap(([label, value]) => (value ? [{ label, value }] : []));
	};
</script>

<RecordDetailView
	{detail}
	back={PAGES.tasks}
	trail={(batch) => [{ label: PAGES.tasks.label, href: tasksTabPath(batch.kind) }, { label: batch.name }]}
	tables={BATCH_TABLES}
	title={(batch) => batch.name}
	description={(batch) => `${textOf(batch).title} · ${batch.outlet_name}`}
>
	{#snippet badge(batch)}
		<Badge tone={batch.is_active ? 'success' : 'warning'}>{batch.is_active ? batchText.statusActive : batchText.statusInactive}</Badge>
		{#if batch.target === TARGET_USER && batch.user.length === 0}
			<Badge tone="warning">{batchText.noRecipient}</Badge>
		{/if}
	{/snippet}
	{#snippet extraActions(batch)}
		<Button label={batch.is_active ? batchText.deactivate : batchText.activate} icon={batch.is_active ? 'eye-off' : 'eye'} disabled={detail.busy} onclick={() => void setActive(batch, !batch.is_active)} />
		<Button label={batchText.copyToBranches} icon="copy" disabled={detail.busy} onclick={() => void openCopy()} />
	{/snippet}
	{#snippet body(batch)}
		{#if batch.target === TARGET_USER && batch.user.length === 0}
			<Banner tone="warning" icon="alert-triangle" title={batchText.noRecipientTitle}>{batchText.noRecipientBody}</Banner>
		{/if}
		<Card flush>
			<div class="flex flex-col gap-4 border-b border-slate-100 p-4 tablet:p-5">
				<FigureList title={batchText.details} figures={rowsOf(batch)} />
				{#if batch.shift_codes.length > 0}
					<div class="flex flex-wrap gap-2">
						{#each batch.shift_codes as code (code.id)}
							<ShiftCodeBadge {code} showTime />
						{/each}
					</div>
				{/if}
			</div>
			<div class="p-4 tablet:p-5">
				<FigureList
					title={format(batchText.itemsWithCount, { count: batch.items.length })}
					empty={batchText.noItems}
					figures={batch.items.map((item, index) => ({
						label: `${index + 1}. ${item.label}`,
						value: `${ITEM_KINDS.find((kind) => kind.value === item.kind)?.label ?? item.kind}${item.required ? '' : ` (${batchText.optional.toLowerCase()})`}`
					}))}
				/>
			</div>
		</Card>
		<Card>
			<section class="flex flex-col gap-2">
				<h3 class="text-sm font-semibold text-slate-800">{batchText.recentRuns}</h3>
				{#if runsError}
					<Banner tone="danger" icon="alert-triangle" title={batchText.recentRunsFailed}>
						{runsError}
						{#snippet action()}
							<Button label={actionText.retry} onclick={() => void loadRuns()} />
						{/snippet}
					</Banner>
				{:else if runsLoading}
					<SkeletonList rows={2} label={batchText.recentRunsLoading} />
				{:else if runs.length === 0}
					<p class="text-xs text-slate-500">{batchText.recentRunsEmpty}</p>
				{:else}
					<ul class="flex flex-col divide-y divide-slate-100 rounded-lg border border-slate-200">
						{#each runs as run (run.id)}
							<li>
								<button type="button" class="flex w-full items-center gap-3 px-3 py-2 text-left text-sm hover:bg-brand-page" onclick={() => void goto(batchRunPath(run.id))}>
									<i class="ti ti-clipboard-check text-base text-slate-500" aria-hidden="true"></i>
									<span class="min-w-0 flex-1">
										<span class="block font-semibold text-slate-800">{formatDate(run.day)} · {formatTime(run.completed_at)}</span>
										<span class="block truncate text-xs text-slate-500">{format(batchText.filledBy, { name: run.completed_by ?? EMPTY_VALUE })}</span>
									</span>
									<Badge tone={run.problems > 0 ? 'danger' : 'success'}>{run.problems > 0 ? format(batchText.problemsCount, { count: run.problems }) : batchText.noProblems}</Badge>
									<i class="ti ti-chevron-right text-base text-slate-500" aria-hidden="true"></i>
								</button>
							</li>
						{/each}
					</ul>
					<p class="text-xs text-slate-500">{batchText.recentRunsHint}</p>
				{/if}
			</section>
			{#if !batch.is_active}
				<p class="mt-3 text-xs text-slate-500">{batchText.inactiveNote}</p>
			{/if}
		</Card>
		{#if copying}
			<BatchCopyDialog {batch} {outlets} result={copyResult} busy={copyBusy} error={copyError} oncopy={(outletIds) => void copy(batch, outletIds)} onclose={() => (copying = false)} />
		{/if}
	{/snippet}
	{#snippet form(props)}
		<BatchForm kind={props.record.kind as BatchKind} batch={props.record} busy={props.busy} error={props.error} fieldErrors={props.fieldErrors} onsave={(body) => props.onsave(body)} onclose={props.onclose} />
	{/snippet}
	{#snippet removeNote(batch)}
		<RichText template={batchText.removeNote} values={{ name: batch.name }} />
	{/snippet}
</RecordDetailView>
