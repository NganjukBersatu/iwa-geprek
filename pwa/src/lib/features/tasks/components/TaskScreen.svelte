<script lang="ts">
	import FloatingPillButton from '$lib/components/button/FloatingPillButton.svelte';
	import IconButton from '$lib/components/button/IconButton.svelte';
	import BatchCard from '$lib/components/card/BatchCard.svelte';
	import SegmentedControl from '$lib/components/choice/SegmentedControl.svelte';
	import SearchField from '$lib/components/field/SearchField.svelte';
	import SectionTitle from '$lib/components/text/SectionTitle.svelte';
	import FailureState from '$lib/components/feedback/FailureState.svelte';
	import LoadingState from '$lib/components/feedback/LoadingState.svelte';
	import ListCard from '$lib/components/card/ListCard.svelte';
	import Notice from '$lib/components/feedback/Notice.svelte';
	import Pagination from '$lib/components/pagination/Pagination.svelte';
	import { current } from '$lib/auth/current.svelte';
	import BatchFormSheet from '$lib/features/batches/components/BatchFormSheet.svelte';
	import BatchManageSheet from '$lib/features/batches/components/BatchManageSheet.svelte';
	import { batchCardText, rangeLabel, type SentAnswer } from '$lib/features/batches/batches';
	import { wibIso } from '$lib/format/datetime';
	import { t } from '$lib/text/t';
	import { TasksState, type TaskFilter } from '../tasks.svelte';
	import TaskDetailSheet from './TaskDetailSheet.svelte';
	import TaskEditSheet from './TaskEditSheet.svelte';
	import TaskFilterSheet from './TaskFilterSheet.svelte';
	import TaskFormSheet from './TaskFormSheet.svelte';
	import TaskRow from './TaskRow.svelte';
	import TaskSourceSheet from './TaskSourceSheet.svelte';
	import { dynamicStyle } from '$lib/platform/dynamic-style';

	const FILTERS: TaskFilter[] = ['belum', 'selesai'];

	let { onSessionExpired }: { onSessionExpired: () => void } = $props();

	const tasks = new TasksState(() => onSessionExpired());
	const ownUserId = $derived(current.session?.user.id ?? '');

	// Dimuat setiap halaman tampil dan setiap app kembali dari latar belakang, agar data tidak basi.
	$effect(() => {
		void tasks.load();
		void tasks.loadBatches();
		const reload = () => {
			if (document.visibilityState !== 'visible') return;
			void tasks.load();
			void tasks.loadBatches();
		};
		document.addEventListener('visibilitychange', reload);
		return () => document.removeEventListener('visibilitychange', reload);
	});

	let selectedId = $state<string | null>(null);
	let creating = $state(false);
	let editing = $state(false);
	let viewingSource = $state(false);
	let filtering = $state(false);
	let fillingBatchId = $state<string | null>(null);
	let managingBatchId = $state<string | null>(null);
	/** Pengisian yang sedang diperbaiki beserta jawaban tersimpannya. */
	let fixing = $state<{ batchId: string; runId: string; answers: SentAnswer[] } | null>(null);
	let search = $state('');

	const selected = $derived(tasks.items.find((task) => task.id === selectedId) ?? null);
	// Kartu tugas outlet dan rutin ikut tab: yang belum diisi di tab pertama, yang selesai di tab kedua; bagian kosong tidak tampil.
	const shownBatches = $derived(tasks.matchingBatches(ownUserId));
	const batchSections = $derived(
		(
			[
				{ title: 'batch_tag', kind: 'outlet' },
				{ title: 'batch_routine_tag', kind: 'routine' }
			] as const
		)
			.map((section) => ({ title: section.title, batches: shownBatches.filter((batch) => batch.kind === section.kind && batch.completed === (tasks.filter === 'selesai')) }))
			.filter((section) => section.batches.length > 0)
	);
	const managing = $derived(tasks.batches.find((batch) => batch.id === managingBatchId) ?? null);
	const fixingBatch = $derived(fixing ? (tasks.batches.find((batch) => batch.id === fixing?.batchId) ?? null) : null);
	const filling = $derived(tasks.batches.find((batch) => batch.id === fillingBatchId) ?? null);
</script>

{#if filling}
	<BatchFormSheet
		batch={filling}
		submitting={tasks.batchSubmitting}
		error={tasks.batchError}
		onSubmit={async (answers) => {
			if (await tasks.completeBatch(filling.id, answers)) fillingBatchId = null;
		}}
		onDismiss={() => {
			tasks.clearBatchError();
			fillingBatchId = null;
		}}
	/>
{/if}

{#if managing && managing.runId}
	{@const batch = managing}
	{@const runId = managing.runId}
	<BatchManageSheet
		{batch}
		submitting={tasks.batchSubmitting}
		error={tasks.batchError}
		onFix={async () => {
			// Nilai kartu dibaca dulu: begitu lembar ini ditutup, kartunya tidak lagi terbaca dari sini.
			const target = { batchId: batch.id, runId };
			const answers = await tasks.loadSentAnswers(target.runId);
			if (!answers) return;
			fixing = { ...target, answers };
			managingBatchId = null;
		}}
		onCancel={async () => {
			const target = runId;
			if (await tasks.cancelBatch(target)) managingBatchId = null;
		}}
		onDelete={async () => {
			const target = runId;
			if (await tasks.deleteBatch(target)) managingBatchId = null;
		}}
		onDismiss={() => {
			tasks.clearBatchError();
			managingBatchId = null;
		}}
	/>
{/if}

{#if fixing && fixingBatch}
	{@const draft = fixing}
	<BatchFormSheet
		batch={fixingBatch}
		submitting={tasks.batchSubmitting}
		error={tasks.batchError}
		initialValues={Object.fromEntries(draft.answers.flatMap((answer) => (answer.value === null ? [] : [[answer.itemId, answer.value]])))}
		keptPhotoUrls={Object.fromEntries(draft.answers.flatMap((answer) => (answer.photoUrl === null ? [] : [[answer.itemId, answer.photoUrl]])))}
		submitLabel={t('batch_fix_submit')}
		onSubmit={async (answers) => {
			if (await tasks.fixBatch(draft.runId, answers)) fixing = null;
		}}
		onDismiss={() => {
			tasks.clearBatchError();
			fixing = null;
		}}
	/>
{/if}

{#if filtering}<TaskFilterSheet {tasks} {ownUserId} onDismiss={() => (filtering = false)} />{/if}

{#if creating}
	<TaskFormSheet
		options={tasks.options}
		submitting={tasks.submitting}
		error={tasks.submitError}
		onSubmit={async (task) => {
			if (await tasks.create(task)) creating = false;
		}}
		onLoadOptions={(outletId) => void tasks.loadOptions(outletId)}
		onDismiss={() => {
			tasks.clearSubmitError();
			creating = false;
		}}
	/>
{/if}

{#if selected}
	{@const task = selected}
	<TaskDetailSheet
		{task}
		submitting={tasks.submitting}
		submitError={tasks.submitError}
		onComplete={async (note, media) => {
			if (await tasks.complete(task.id, note, media)) selectedId = null;
		}}
		onAddAttachments={(media) => void tasks.addAttachments(task.id, media)}
		onFixNote={(note) => void tasks.fixNote(task.id, note)}
		onRemoveAttachment={(attachment) => void tasks.removeAttachment(task.id, attachment.id)}
		onEdit={() => (editing = true)}
		onOpenSource={() => (viewingSource = true)}
		onDelete={async () => {
			if (await tasks.delete(task.id)) selectedId = null;
		}}
		onDismiss={() => {
			tasks.clearSubmitError();
			viewingSource = false;
			selectedId = null;
		}}
	/>
	{#if viewingSource}
		<TaskSourceSheet taskId={task.id} {onSessionExpired} onDismiss={() => (viewingSource = false)} />
	{/if}
	{#if editing}
		<TaskEditSheet
			{task}
			submitting={tasks.submitting}
			error={tasks.submitError}
			onSubmit={async (title, description, due) => {
				if (await tasks.update(task.id, title, description, due ? wibIso(due.date, due.time) : null)) editing = false;
			}}
			onDismiss={() => {
				tasks.clearSubmitError();
				editing = false;
			}}
		/>
	{/if}
{/if}

<div class="relative flex size-full justify-center">
	<div class="size-full max-w-[var(--size-content-max)] overflow-y-auto" use:dynamicStyle={{ padding: '16px var(--page-padding)' }}>
		<div class="flex w-full flex-col gap-3">
			<div class="flex items-end gap-2">
				<div class="min-w-0 flex-1"><SearchField bind:value={search} label={t('tasks_search_label')} oninput={() => tasks.setSearch(search)} /></div>
				<IconButton
					icon="Adjustments"
					label={t('tasks_filter_open')}
					onclick={() => (filtering = true)}
					tint="on-primary"
					badge={tasks.activeFilterCount > 0 ? String(tasks.activeFilterCount) : null}
					container="primary"
					badgeColor="accent"
					onBadgeColor="content"
				/>
			</div>

			<SegmentedControl options={[t('tasks_filter_pending'), t('tasks_filter_done')]} selectedIndex={FILTERS.indexOf(tasks.filter)} onselect={(index) => tasks.setFilter(FILTERS[index] ?? 'belum')} />

			{#each batchSections as section (section.title)}
				<SectionTitle text={t(section.title)} />
				{#each section.batches as batch (batch.id)}
					{@const card = batchCardText(batch)}
					<BatchCard
						title={batch.name}
						rangeLabel={rangeLabel(batch)}
						completed={batch.completed}
						tone={card.tone}
						icon={card.icon}
						note={card.fill ? t(card.fill) : null}
						tagLabel={t(card.tag)}
						fillLabel={t('batch_fill')}
						doneLabel={t(card.done)}
						manageLabel={t('batch_manage_action')}
						onFill={() => (fillingBatchId = batch.id)}
						onManage={batch.runId && (batch.canFix || batch.canCancel || batch.canDelete) ? () => (managingBatchId = batch.id) : undefined}
					/>
				{/each}
			{/each}

			<SectionTitle text={t('tasks_section_personal')} />

			{#if tasks.loading}
				<LoadingState />
			{:else if tasks.failure}
				<FailureState failure={tasks.failure} onRetry={() => void tasks.load()} />
			{:else}
				{#if tasks.items.length === 0}
					<ListCard><Notice text={t('tasks_empty')} /></ListCard>
				{:else}
					{#each tasks.items as task (task.id)}
						<TaskRow {task} onclick={() => (selectedId = task.id)} />
					{/each}
					{#if tasks.pageCount > 1}
						<Pagination page={Math.min(Math.max(tasks.page, 0), tasks.pageCount - 1)} pageCount={tasks.pageCount} onPageChange={(page) => tasks.setPage(page)} />
					{/if}
				{/if}
			{/if}
			<div class="h-16"></div>
		</div>
	</div>
	<div class="absolute bottom-4" use:dynamicStyle={{ right: 'var(--page-padding)' }}>
		<FloatingPillButton icon="Plus" label={t('tasks_add_short')} onclick={() => (creating = true)} />
	</div>
</div>
