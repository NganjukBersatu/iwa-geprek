<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount, untrack } from 'svelte';
	import { api } from '$lib/api';
	import type { BatchAnswer, BatchRunDetail, BatchRunVersion } from '$lib/api/types';
	import { userMessage } from '$lib/api/user-message';
	import { access } from '$lib/auth/access.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import FigureList from '$lib/components/card/FigureList.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import ConfirmDialog from '$lib/components/dialog/ConfirmDialog.svelte';
	import { toast } from '$lib/components/feedback/toast.svelte';
	import PageIntro from '$lib/components/header/PageIntro.svelte';
	import AttachmentGallery from '$lib/components/media/AttachmentGallery.svelte';
	import SkeletonList from '$lib/components/skeleton/SkeletonList.svelte';
	import { formatDate } from '$lib/date/range';
	import { EMPTY_VALUE } from '$lib/format/currency';
	import { formatDateTime, formatTime } from '$lib/format/datetime';
	import { live } from '$lib/live/live';
	import { PAGES, taskNewPath, tasksTabPath } from '$lib/nav/pages';
	import { actionText } from '$lib/text/actions';
	import { batchRunText } from '$lib/text/batch-runs';
	import { format } from '$lib/text/format';
	import { RUN_TABLES } from '../runs.svelte';
	import { answerText, changeLabel, PHOTO_KIND } from '../constants';
	import { RunEditor } from '../run-editor.svelte';
	import BatchRunFixDialog from './BatchRunFixDialog.svelte';

	let { id }: { id: string } = $props();

	let detail = $state<BatchRunDetail | null>(null);
	let loading = $state(true);
	let error = $state('');
	let openVersion = $state<number | null>(null);
	let token = 0;

	const editor = new RunEditor((action) => {
		if (action === 'delete' || action === 'cancel') toast.show(action === 'delete' ? batchRunText.deleted : batchRunText.cancelled);
		else toast.show(batchRunText.fixed);
		void load(true);
	});

	async function load(quiet = false): Promise<void> {
		const mine = ++token;
		if (!quiet) loading = true;
		try {
			const found = await api.batches.run(untrack(() => id));
			if (mine !== token) return;
			detail = found;
			error = '';
		} catch (failure) {
			if (mine !== token || quiet) return;
			detail = null;
			error = userMessage(failure, batchRunText.loadFailed);
		} finally {
			if (mine === token) loading = false;
		}
	}

	onMount(() => {
		void load();
		return live.on(RUN_TABLES, () => void load(true));
	});

	const canManage = $derived(access.allows('manage_tasks'));
	const changed = $derived(detail?.last_action ? changeLabel(detail.last_action, detail.fixed_by) : '');
	const changedAt = $derived(detail?.fixed_at && changed ? format(batchRunText.changedAt, { changed, time: formatDateTime(detail.fixed_at) }) : changed);
	const answered = (answer: BatchAnswer): boolean => answer.kind !== PHOTO_KIND;
	const photosOf = (answers: { label: string; photo_url: string | null }[], prefix: string) =>
		answers.flatMap((answer, index) => (answer.photo_url ? [{ id: `${prefix}${index}`, kind: 'photo', url: answer.photo_url, removable: false, label: answer.label }] : []));
	const answersOf = (answers: BatchAnswer[]) => answers.filter(answered).map((answer) => ({ label: answer.label, value: answerText(answer.kind, answer.value) }));
	const versionAnswers = (version: BatchRunVersion) => answersOf(version.answers);
</script>

{#if error}
	<Banner tone="danger" icon="alert-triangle" title={batchRunText.loadFailed}>
		{error}
		{#snippet action()}
			<Button label={actionText.retry} onclick={() => void load()} />
		{/snippet}
	</Banner>
{:else if loading && !detail}
	<SkeletonList rows={4} label={batchRunText.loadingDetail} />
{:else if detail}
	{@const run = detail}
	<div class="flex flex-col gap-4 tablet:gap-6">
		<PageIntro title={run.batch_name} description={`${run.outlet_name} · ${formatDate(run.day)}`} items={[{ label: PAGES.tasks.label, href: tasksTabPath('history') }, { label: run.batch_name }]}>
			{#snippet badge()}
				{#if run.problems > 0}<Badge tone="danger">{format(batchRunText.problemsBadge, { count: run.problems })}</Badge>{/if}
				{#if run.last_action}<Badge tone="warning">{changedAt}</Badge>{/if}
			{/snippet}
			{#snippet actions()}
				{#if canManage && run.last_action !== 'delete'}
					<Button label={batchRunText.remove} icon="trash" variant="danger" disabled={editor.busy} onclick={() => editor.ask('delete')} />
					{#if !run.cancelled}
						{#if run.follow_up_total === 0}
							<Button label={batchRunText.cancel} icon="arrow-back-up" disabled={editor.busy} onclick={() => editor.ask('cancel')} />
						{/if}
						<Button label={editor.busy && !editor.confirming ? batchRunText.fixLoading : batchRunText.fix} icon="pencil" disabled={editor.busy} onclick={() => void editor.openFix(run.id)} />
					{/if}
				{/if}
				{#if canManage && !run.cancelled}
					<Button label={run.follow_up_total > 0 ? batchRunText.followUpAgain : batchRunText.followUp} icon="user-plus" variant="primary" onclick={() => void goto(taskNewPath(run.id))} />
				{/if}
			{/snippet}
		</PageIntro>

		{#if run.cancelled}
			<Banner tone="warning" icon="alert-triangle" title={run.last_action === 'delete' ? batchRunText.deletedTitle : batchRunText.cancelledTitle}>
				{format(run.last_action === 'delete' ? batchRunText.deletedBody : batchRunText.cancelledBody, { changed: changedAt })}
			</Banner>
		{/if}
		{#if editor.error && !editor.stored && !editor.confirming}
			<Banner tone="danger" icon="alert-triangle">{editor.error}</Banner>
		{/if}

		<Card flush class="grid laptop:grid-cols-2">
			<div class="border-b border-slate-100 p-4 tablet:p-5 laptop:border-b-0 laptop:border-r">
				<FigureList
					title={batchRunText.summary}
					figures={[
						{ label: batchRunText.date, value: formatDate(run.day) },
						{ label: batchRunText.branch, value: run.outlet_name },
						{ label: batchRunText.filledBy, value: run.completed_by ?? EMPTY_VALUE },
						{ label: batchRunText.doneAtTime, value: formatTime(run.completed_at) }
					]}
				/>
			</div>
			<div class="p-4 tablet:p-5">
				<FigureList title={batchRunText.answers} empty={batchRunText.versionNoContent} figures={answersOf(run.answers)} />
			</div>
		</Card>

		{#each photosOf(run.answers, '') as photo (photo.id)}
			<Card>
				<section class="flex flex-col gap-2">
					<h3 class="text-sm font-semibold text-slate-800">{photo.label}</h3>
					<AttachmentGallery attachments={[photo]} alt={photo.label} />
				</section>
			</Card>
		{/each}

		{#if run.follow_ups.length > 0}
			<Card>
				<section class="flex flex-col gap-2">
					<h3 class="text-sm font-semibold text-slate-800">{format(batchRunText.followUps, { count: run.follow_up_total })}</h3>
					<ul class="flex flex-col divide-y divide-slate-100 rounded-lg border border-slate-200">
						{#each run.follow_ups as item (item.task_id)}
							<li class="flex items-center gap-3 px-3 py-2 text-sm">
								<span class="flex size-7 shrink-0 items-center justify-center rounded-full bg-brand-soft text-xs font-semibold text-brand">{item.number}</span>
								<span class="min-w-0 flex-1">
									<span class="block truncate font-semibold text-slate-800">{item.title}</span>
									<span class="block truncate text-xs text-slate-500">
										{format(batchRunText.followUpFor, { name: item.assignee_name ?? EMPTY_VALUE })}{item.due_at ? format(batchRunText.followUpDue, { time: formatDateTime(item.due_at) }) : ''}{item.completed_at ? format(batchRunText.followUpDone, { time: formatDateTime(item.completed_at) }) : ''}
									</span>
								</span>
								<Badge tone={item.done ? 'success' : 'warning'}>{item.done ? batchRunText.followUpFinished : batchRunText.followUpPending}</Badge>
							</li>
						{/each}
					</ul>
					{#if run.follow_up_total > run.follow_ups.length}
						<p class="text-xs text-slate-500">{format(batchRunText.followUpShown, { shown: run.follow_ups.length, total: run.follow_up_total })}</p>
					{/if}
				</section>
			</Card>
		{/if}

		{#if run.versions.length > 0}
			<Card>
				<section class="flex flex-col gap-2">
					<h3 class="text-sm font-semibold text-slate-800">{format(batchRunText.history, { count: run.version_count })}</h3>
					<ul class="flex flex-col divide-y divide-slate-100 rounded-lg border border-slate-200">
						{#each run.versions as version (version.number)}
							{@const open = openVersion === version.number}
							{@const old = versionAnswers(version)}
							{@const oldPhotos = photosOf(version.answers, `${version.number}-`)}
							<li>
								<button type="button" class="flex w-full items-center gap-3 px-3 py-2 text-left text-sm hover:bg-brand-page" aria-expanded={open} onclick={() => (openVersion = open ? null : version.number)}>
									<span class="min-w-0 flex-1">
										<span class="block font-semibold text-slate-800">{changeLabel(version.action, version.changed_by)}</span>
										<span class="block truncate text-xs text-slate-500">{formatDateTime(version.changed_at)}</span>
									</span>
									<i class="ti ti-chevron-down text-base text-slate-500 {open ? 'rotate-180' : ''}" aria-hidden="true"></i>
								</button>
								{#if open}
									<div class="flex flex-col gap-3 border-t border-slate-100 px-3 py-3">
										{#if old.length === 0 && oldPhotos.length === 0}
											<p class="text-xs text-slate-500">{batchRunText.versionNoContent}</p>
										{:else}
											<p class="text-xs text-slate-500">{format(batchRunText.versionContent, { name: version.completed_by ?? EMPTY_VALUE, time: formatDateTime(version.completed_at) })}</p>
											{#if old.length > 0}<FigureList figures={old} />{/if}
											{#each oldPhotos as photo (photo.id)}
												<div class="flex flex-col gap-1">
													<span class="text-xs font-semibold text-slate-600">{photo.label}</span>
													<AttachmentGallery attachments={[photo]} alt={photo.label} />
												</div>
											{/each}
										{/if}
									</div>
								{/if}
							</li>
						{/each}
					</ul>
					{#if run.version_count > run.versions.length}
						<p class="text-xs text-slate-500">{format(batchRunText.historyShown, { shown: run.versions.length, total: run.version_count })}</p>
					{/if}
				</section>
			</Card>
		{/if}
	</div>

	{#if editor.stored}
		<BatchRunFixDialog stored={editor.stored} busy={editor.busy} error={editor.error} onsave={(answers) => void editor.saveFix(run.id, answers)} onclose={() => editor.close()} />
	{/if}
	<ConfirmDialog open={editor.confirming === 'cancel'} title={format(batchRunText.cancelTitle, { name: run.batch_name })} confirmLabel={batchRunText.cancelConfirm} busy={editor.busy} error={editor.error} onconfirm={() => void editor.confirm(run.id)} oncancel={() => editor.close()}>
		{batchRunText.cancelBody}
	</ConfirmDialog>
	<ConfirmDialog open={editor.confirming === 'delete'} title={format(batchRunText.deleteTitle, { name: run.batch_name })} confirmLabel={batchRunText.deleteConfirm} danger busy={editor.busy} error={editor.error} onconfirm={() => void editor.confirm(run.id)} oncancel={() => editor.close()}>
		<p>{batchRunText.deleteBody}</p>
		{#if run.follow_up_total > 0}
			<p class="mt-2">{format(batchRunText.deleteFollowUps, { count: run.follow_up_total })}</p>
		{/if}
	</ConfirmDialog>
{:else}
	<Notice loading text={batchRunText.loadingDetail} />
{/if}
