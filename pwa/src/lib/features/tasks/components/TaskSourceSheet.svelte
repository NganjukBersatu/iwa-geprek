<script lang="ts">
	import type { AppFailure } from '$lib/failure/failure';
	import DetailList from '$lib/components/card/DetailList.svelte';
	import type { DetailListRow } from '$lib/components/card/types';
	import FailureState from '$lib/components/feedback/FailureState.svelte';
	import LoadingState from '$lib/components/feedback/LoadingState.svelte';
	import StatusBadge from '$lib/components/feedback/StatusBadge.svelte';
	import AttachmentGallery from '$lib/components/media/AttachmentGallery.svelte';
	import BottomSheet from '$lib/components/sheet/BottomSheet.svelte';
	import SectionTitle from '$lib/components/text/SectionTitle.svelte';
	import { TOGGLE_OK, TOGGLE_PROBLEM } from '$lib/features/batches/batches';
	import { longDateLabel, whenLabel } from '$lib/format/labels';
	import { t } from '$lib/text/t';
	import { taskSourceRun, type SourceRun } from '../source-run';

	const PHOTO_KIND = 'photo';
	const TOGGLE_KIND = 'toggle';

	/** Pengisian yang ditindaklanjuti sebuah tugas: rincian, jawaban, dan fotonya, supaya pelaksana melihat sendiri masalah yang harus dibereskan. */
	let { taskId, onSessionExpired, onDismiss }: { taskId: string; onSessionExpired: () => void; onDismiss: () => void } = $props();

	let run = $state<SourceRun | null>(null);
	let failure = $state<AppFailure | null>(null);
	let loading = $state(true);

	async function load(): Promise<void> {
		loading = true;
		failure = null;
		const result = await taskSourceRun(taskId);
		loading = false;
		if (result.kind === 'unauthorized') return onSessionExpired();
		if (result.kind === 'failure') return void (failure = result.failure);
		run = result.value;
	}

	$effect(() => {
		void load();
	});

	const summary = $derived<DetailListRow[]>(
		run
			? [
					{ label: t('tasks_detail_name'), value: run.name },
					{ label: t('tasks_detail_outlet'), value: run.outletName },
					{ label: t('tasks_source_day'), value: longDateLabel(run.day) },
					...(run.filler ? [{ label: t('tasks_source_filler'), value: run.filler }] : []),
					...(run.doneAt ? [{ label: t('tasks_source_done_at'), value: whenLabel(run.doneAt) }] : [])
				]
			: []
	);
	const answers = $derived<DetailListRow[]>(
		(run?.answers ?? [])
			.filter((answer) => answer.kind !== PHOTO_KIND)
			.map((answer) => {
				if (answer.kind === TOGGLE_KIND && answer.value === TOGGLE_PROBLEM) return { label: answer.label, valueContent: problemBadge };
				if (answer.kind === TOGGLE_KIND && answer.value === TOGGLE_OK) return { label: answer.label, valueContent: okBadge };
				return { label: answer.label, value: answer.value ?? t('tasks_source_empty_answer') };
			})
	);
	const photos = $derived((run?.answers ?? []).flatMap((answer, index) => (answer.photoUrl ? [{ label: answer.label, attachment: { id: String(index), isVideo: false, url: answer.photoUrl, removable: false } }] : [])));
</script>

{#snippet okBadge()}<StatusBadge text={t('batch_toggle_ok')} tone="positive" />{/snippet}
{#snippet problemBadge()}<StatusBadge text={t('batch_toggle_problem')} tone="danger" />{/snippet}

<BottomSheet title={t('tasks_source_title')} {onDismiss}>
	<div class="flex w-full flex-col gap-3">
		{#if loading}
			<LoadingState rows={4} />
		{:else if failure}
			<FailureState {failure} onRetry={() => void load()} />
		{:else if run}
			{#if run.problems > 0}
				<div><StatusBadge text={t('tasks_source_problems', run.problems)} tone="danger" /></div>
			{/if}
			<DetailList rows={summary} />
			{#if answers.length > 0}<DetailList rows={answers} />{/if}
			{#each photos as photo (photo.attachment.id)}
				<SectionTitle text={photo.label} />
				<AttachmentGallery attachments={[photo.attachment]} />
			{/each}
		{/if}
	</div>
</BottomSheet>
