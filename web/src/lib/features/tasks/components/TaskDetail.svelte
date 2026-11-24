<script lang="ts">
	import { untrack } from 'svelte';
	import { api } from '$lib/api';
	import type { Task, TaskAttachment } from '$lib/api/types';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import FigureList from '$lib/components/card/FigureList.svelte';
	import { toast } from '$lib/components/feedback/toast.svelte';
	import MediaField from '$lib/components/form/MediaField.svelte';
	import TextArea from '$lib/components/form/TextArea.svelte';
	import AttachmentGallery from '$lib/components/media/AttachmentGallery.svelte';
	import { EMPTY_VALUE } from '$lib/format/currency';
	import { formatDateTime } from '$lib/format/datetime';
	import { TASK_TABLES } from '$lib/live/tables';
	import { PAGES, batchRunPath, taskNewPath } from '$lib/nav/pages';
	import { goto } from '$app/navigation';
	import RichText from '$lib/components/text/RichText.svelte';
	import { formatDate } from '$lib/date/range';
	import { recordText } from '$lib/text/record-detail';
	import RecordDetailView from '../../record-detail/components/RecordDetailView.svelte';
	import { RecordDetailState } from '../../record-detail/record-detail.svelte';
	import { isLate, ownerLabel } from '../display';
	import { personName } from '../tasks.svelte';
	import TaskForm from './TaskForm.svelte';
	import type { TaskInput } from '$lib/api/types';
	import { termText } from '$lib/text/terms';
	import { taskText } from '$lib/text/tasks';
	import { format } from '$lib/text/format';

	let { id }: { id: string } = $props();

	const detail = new RecordDetailState<Task, TaskInput>(untrack(() => id), {
		load: (taskId) => api.tasks.get(taskId),
		update: (task, input) => api.tasks.update(task.id, { title: input.title, description: input.description, due_at: input.due_at }),
		remove: (task) => api.tasks.remove(task.id),
		name: (task) => task.title,
		text: recordText('tugas', PAGES.tasks.label)
	});

	let note = $state('');
	let proof = $state<File[]>([]);
	let extra = $state<File[]>([]);
	// The completion note being corrected; it starts from the saved one.
	let fixedNote = $state('');
	$effect(() => {
		fixedNote = detail.record?.completion_note ?? '';
	});

	async function fixNote(): Promise<void> {
		const text = fixedNote.trim();
		if (await change((current) => api.tasks.fixCompletion(current.id, text), taskText.fixNoteFailed, taskText.fixNoteSaved)) fixedNote = text;
	}

	/** Runs one action on the task, then shows the task the server answers with. */
	async function change(work: (task: Task) => Promise<Task>, failure: string, success?: string): Promise<boolean> {
		const done = await detail.change(work, failure);
		if (done && success) toast.show(success);
		return done;
	}

	async function complete(task: Task): Promise<void> {
		if (await change((current) => api.tasks.complete(current.id, note.trim(), proof), taskText.completeFailed, format(taskText.taskCompleted, { title: task.title }))) {
			note = '';
			proof = [];
		}
	}

	async function addExtra(): Promise<void> {
		if (await change((current) => api.tasks.addAttachments(current.id, extra), taskText.attachmentAddFailed)) extra = [];
	}

	const removeFile = (attachment: TaskAttachment) => change((current) => api.tasks.removeAttachment(current.id, attachment.id), taskText.attachmentRemoveFailed);
</script>

<RecordDetailView
	{detail}
	back={PAGES.tasks}
	trail={(task) => [{ label: PAGES.tasks.label, href: PAGES.tasks.path }, { label: task.title }]}
	tables={TASK_TABLES}
	title={(task) => task.title}
	description={(task) => task.outlet?.name ?? ''}
	editable={(task) => task.can_edit}
	removable={(task) => task.can_edit}
>
	{#snippet badge(task)}
		<Badge tone={task.status === 'selesai' ? 'success' : 'warning'}>{task.status === 'selesai' ? taskText.done : taskText.notDone}</Badge>
		{#if isLate(task)}<Badge tone="danger">{taskText.overdue}</Badge>{/if}
	{/snippet}
	{#snippet body(task)}
		{#if task.source_run}
			<Card>
				<section class="flex flex-col gap-2">
					<p class="text-xs text-slate-600">
						<RichText template={taskText.followUpOf} values={{ number: task.follow_up_number ?? 1, total: task.follow_up_total ?? 1, name: task.source_run.batch_name, day: formatDate(task.source_run.day) }} />
					</p>
					<div class="flex flex-wrap gap-2">
						<Button label={taskText.viewSourceRun} icon="clipboard-check" compact onclick={() => void goto(batchRunPath(task.source_run!.id))} />
						{#if task.can_edit}
							<Button label={taskText.followUpAgain} icon="user-plus" compact onclick={() => void goto(taskNewPath(task.source_run!.id))} />
						{/if}
					</div>
				</section>
			</Card>
		{/if}
		<Card flush class="grid laptop:grid-cols-2">
			<div class="flex flex-col gap-4 border-b border-slate-100 p-4 tablet:p-5 laptop:border-b-0 laptop:border-r">
				<FigureList
					title={taskText.details}
					figures={[
						{ label: taskText.assignedTo, value: ownerLabel(task) },
						{ label: taskText.createdBy, value: personName(task.creator) || EMPTY_VALUE },
						{ label: taskText.deadline, value: task.due_at ? formatDateTime(task.due_at) : EMPTY_VALUE },
						{ label: taskText.completedAt, value: task.completed_at ? formatDateTime(task.completed_at) : EMPTY_VALUE }
					]}
				/>
				<section class="flex flex-col gap-1 border-t border-slate-100 pt-4 text-xs">
					<h3 class="font-semibold text-slate-600">{termText.remark}</h3>
					<p class="whitespace-pre-line {task.description ? 'text-slate-700' : 'text-slate-500'}">{task.description || termText.noRemark}</p>
				</section>
				{#if task.completion_note}
					<section class="flex flex-col gap-1 border-t border-slate-100 pt-4 text-xs">
						<h3 class="font-semibold text-slate-600">{taskText.completionNote}</h3>
						<p class="whitespace-pre-line text-slate-700">{task.completion_note}</p>
					</section>
				{/if}
			</div>
			<div class="flex flex-col gap-4 p-4 tablet:p-5">
				<section class="flex flex-col gap-2">
					<h3 class="text-sm font-semibold text-slate-800">{taskText.attachmentsAndProof}</h3>
					{#if task.attachments.length > 0}
						<AttachmentGallery attachments={task.attachments} alt={format(taskText.attachmentsOf, { title: task.title })} onremove={task.can_edit || task.can_fix ? (attachment) => void removeFile(attachment) : undefined} disabled={detail.busy} />
					{:else}
						<p class="text-xs text-slate-500">{taskText.noAttachments}</p>
					{/if}
				</section>
				{#if task.can_complete}
					<section class="flex flex-col gap-3 border-t border-slate-100 pt-4">
						<h3 class="text-sm font-semibold text-slate-800">{taskText.completeTask}</h3>
						<TextArea label={taskText.noteOptional} bind:value={note} rows={2} maxlength={2000} />
						<MediaField label={taskText.workProof} bind:files={proof} disabled={detail.busy} hint={taskText.proofRequiredHint} />
						<Button label={taskText.complete} icon="check" variant="primary" class="self-start" disabled={detail.busy || proof.length === 0} onclick={() => void complete(task)} />
					</section>
				{:else if task.can_edit || task.can_fix}
					<section class="flex flex-col gap-2 border-t border-slate-100 pt-4">
						{#if task.can_fix}
							<p class="text-xs text-slate-500">{taskText.fixNoteIntro}</p>
							<TextArea label={taskText.fixNoteLabel} bind:value={fixedNote} rows={2} maxlength={2000} />
							{#if fixedNote.trim() !== (task.completion_note ?? '')}
								<Button label={taskText.fixNoteSave} icon="device-floppy" variant="tertiary" class="self-start" disabled={detail.busy} onclick={() => void fixNote()} />
							{/if}
						{/if}
						<MediaField label={taskText.addAttachment} bind:files={extra} disabled={detail.busy} />
						{#if extra.length > 0}
							<Button label={taskText.saveAttachment} icon="upload" variant="tertiary" class="self-start" disabled={detail.busy} onclick={() => void addExtra()} />
						{/if}
					</section>
				{/if}
			</div>
		</Card>
	{/snippet}
	{#snippet form(props)}
		<TaskForm task={props.record} options={null} assignees={[]} busy={props.busy} error={props.error} fieldErrors={props.fieldErrors} onbranch={() => {}} onsave={(input) => props.onsave(input)} onclose={props.onclose} />
	{/snippet}
	{#snippet removeNote()}
		{taskText.removeNote}
	{/snippet}
</RecordDetailView>
