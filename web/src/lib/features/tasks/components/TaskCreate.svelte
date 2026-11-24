<script lang="ts">
	import { untrack } from 'svelte';
	import { api } from '$lib/api';
	import type { Task, TaskInput, TaskOptions, TaskPerson } from '$lib/api/types';
	import { PAGES, taskPath } from '$lib/nav/pages';
	import { createText } from '$lib/text/record-detail';
	import RecordCreateView from '../../record-detail/components/RecordCreateView.svelte';
	import { RecordCreateState } from '../../record-detail/record-create.svelte';
	import { formatDate } from '$lib/date/range';
	import { formatTime } from '$lib/format/datetime';
	import { followUpOf, type FollowUp } from '../../batches/constants';
	import TaskForm from './TaskForm.svelte';
	import { taskText } from '$lib/text/tasks';
	import { format } from '$lib/text/format';

	/** The filling this task follows up, when the page was opened from one. */
	let { sourceRunId = null }: { sourceRunId?: string | null } = $props();

	type TaskSave = { input: TaskInput; files: File[] };

	/** Who a new task can be given to; follows the branch chosen in the form. */
	let assignees = $state<TaskPerson[]>([]);

	async function loadAssignees(outletId: string): Promise<void> {
		try {
			assignees = (await api.tasks.options(outletId ? { outlet_id: outletId } : {})).assignees;
		} catch {
			assignees = [];
		}
	}

	let prefill = $state<FollowUp | null>(null);

	/** The title, remark, and branch of the follow-up come from the filling; when it cannot be read the task is made without them. */
	async function loadPrefill(runId: string): Promise<void> {
		try {
			const run = await api.batches.run(runId);
			prefill = followUpOf(run, `${formatDate(run.day)} ${formatTime(run.completed_at)}`);
			await loadAssignees(prefill.outletId);
		} catch {
			prefill = null;
		}
	}

	const create = new RecordCreateState<Task, TaskSave, TaskOptions>({
		context: async () => {
			const options = await api.tasks.options();
			assignees = options.assignees;
			const source = untrack(() => sourceRunId);
			if (source) await loadPrefill(source);
			return options;
		},
		create: ({ input, files }) => api.tasks.create(input, files),
		name: (task) => task.title,
		message: (task) => (task.status === 'selesai' ? format(taskText.taskRecordedDone, { title: task.title }) : format(taskText.taskCreated, { title: task.title })),
		after: (task) => taskPath(task.id),
		text: createText('tugas')
	});
</script>

<RecordCreateView {create} back={PAGES.tasks}>
	{#snippet form(props)}
		<TaskForm
			task={null}
			options={props.context}
			{assignees}
			{prefill}
			busy={props.busy}
			error={props.error}
			fieldErrors={props.fieldErrors}
			onbranch={(id) => void loadAssignees(id)}
			onsave={(input, files) => props.onsave({ input, files })}
			onclose={props.onclose}
		/>
	{/snippet}
</RecordCreateView>
