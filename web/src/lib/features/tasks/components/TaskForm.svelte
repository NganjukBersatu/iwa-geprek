<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import { untrack } from 'svelte';
	import type { Task, TaskInput, TaskOptions, TaskPerson } from '$lib/api/types';
	import Banner from '$lib/components/card/Banner.svelte';
	import BranchField from '$lib/components/form/BranchField.svelte';
	import CheckRow from '$lib/components/form/CheckRow.svelte';
	import FormPage from '$lib/components/form/FormPage.svelte';
	import FormSection from '$lib/components/form/FormSection.svelte';
	import MediaField from '$lib/components/form/MediaField.svelte';
	import SelectField from '$lib/components/form/SelectField.svelte';
	import TextArea from '$lib/components/form/TextArea.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import { FieldErrors, focusRefused } from '$lib/components/form/field-errors.svelte';
	import { fromWibInput, toWibInput } from '$lib/date/wib';
	import { PAGES, taskPath } from '$lib/nav/pages';
	import type { FollowUp } from '../../batches/constants';
	import { personName } from '../tasks.svelte';
	import { termText } from '$lib/text/terms';
	import { actionText } from '$lib/text/actions';
	import { taskText } from '$lib/text/tasks';
	import { format } from '$lib/text/format';

	let {
		task,
		options,
		assignees,
		prefill = null,
		busy,
		error,
		fieldErrors = {},
		onbranch,
		onsave,
		onclose
	}: {
		task: Task | null;
		options: TaskOptions | null;
		assignees: TaskPerson[];
		/** A new task that follows up a filling: its title, remark, and branch are put in, and it goes to an employee. */
		prefill?: FollowUp | null;
		busy: boolean;
		error: string;
		/** What the server refused, by field name, shown under the field itself. */
		fieldErrors?: Record<string, string>;
		onbranch: (outletId: string) => void;
		onsave: (input: TaskInput, files: File[]) => void;
		onclose: () => void;
	} = $props();

	const current = untrack(() => task);
	const trail = [
		{ label: PAGES.tasks.label, href: PAGES.tasks.path },
		...(current ? [{ label: current.title, href: taskPath(current.id) }, { label: actionText.edit }] : [{ label: taskText.addTask }])
	];
	const outlets = $derived(options?.outlets ?? []);
	const canManage = $derived(options?.can_manage === true);
	const targets = [
		{ value: 'self', label: taskText.myself },
		{ value: 'employee', label: termText.employee }
	];

	const start = untrack(() => prefill);
	let mode = $state(start ? 'employee' : 'self');
	let outlet = $state(start?.outletId ?? '');
	let assignee = $state('');
	let title = $state(current?.title ?? start?.title ?? '');
	let description = $state(current?.description ?? start?.description ?? '');
	let due = $state(toWibInput(current?.due_at ?? null));
	let files = $state<File[]>([]);
	let finished = $state(false);

	const choosesOutlet = $derived(canManage && mode === 'employee' && outlets.length > 1);
	const errors = new FieldErrors(
		{ title: taskText.taskTitle, due_at: taskText.deadline, description: termText.remark, mode: taskText.taskFor, outlet_id: termText.branch, assignee_id: termText.employee, files: taskText.attachments },
		() => fieldErrors
	);

	// A refusal from the server puts the cursor in the first refused box.
	$effect(() => {
		if (Object.keys(fieldErrors).length > 0) void focusRefused();
	});

	function submit(): void {
		const found: Record<string, string> = {};
		if (!title.trim()) found.title = taskText.titleRequired;
		if (!current && choosesOutlet && !outlet) found.outlet_id = taskText.branchRequired;
		if (!current && mode === 'employee' && !assignee) found.assignee_id = taskText.employeeRequired;
		if (!current && finished && files.length === 0) found.files = taskText.completedNeedsProof;
		if (!errors.check(found)) return;
		onsave(
			{
				title: title.trim(),
				description: description.trim(),
				assignee_id: mode === 'employee' ? assignee : null,
				due_at: fromWibInput(due),
				complete: finished && mode === 'self',
				source_run_id: start?.sourceRunId ?? null
			},
			files
		);
	}
</script>

<FormPage
	title={current ? format(controlText.editName, { name: current.title }) : taskText.addTask}
	description={taskText.formDescription}
	stacked
	{trail}
	{busy}
	{onclose}
>
	<FormSection icon="checklist" title={taskText.task} description={taskText.taskSectionDescription}>
		<div class="grid gap-2 tablet:grid-cols-2">
			<TextField label={taskText.taskTitle} bind:value={title} maxlength={200} required error={errors.get('title')} />
			<TextField label={taskText.deadlineWib} type="datetime-local" bind:value={due} hint={current ? taskText.deadlineCannotClear : taskText.emptyMeansNoDeadline} error={errors.get('due_at')} />
		</div>
		<TextArea label={termText.remark} bind:value={description} rows={3} maxlength={2000} error={errors.get('description')} />
	</FormSection>
	{#if !current}
		{#if canManage}
			<FormSection icon="user" title={taskText.forWhom} description={taskText.forWhomDescription}>
				<div class="grid gap-2 tablet:grid-cols-3">
					<SelectField
						label={taskText.taskFor}
						bind:value={mode}
						options={targets}
						onchange={() => {
							finished = false;
							assignee = '';
						}}
					/>
					{#if choosesOutlet}
						<BranchField
							bind:value={outlet}
							error={errors.get('outlet_id')}
							onchange={(id) => {
								assignee = '';
								onbranch(id);
							}}
						/>
					{/if}
					{#if mode === 'employee'}
						<SelectField label={termText.employee} bind:value={assignee} empty={taskText.chooseEmployee} required options={assignees.map((person) => ({ value: person.id, label: `${personName(person)} · ${person.role_name}` }))} error={errors.get('assignee_id')} />
					{/if}
				</div>
			</FormSection>
		{/if}
		<FormSection icon="photo" title={taskText.attachments} description={taskText.attachmentsHint}>
			<div class="flex flex-col gap-1" tabindex="-1" aria-invalid={errors.get('files') ? true : undefined}>
				<MediaField label={taskText.exampleOrAttachment} bind:files disabled={busy} />
			</div>
			{#if errors.get('files')}<p class="text-xs text-danger-700" role="alert">{errors.get('files')}</p>{/if}
			{#if mode === 'self'}
				<CheckRow label={taskText.markDoneNow} hint={taskText.markDoneNowHint} checked={finished} onchange={() => (finished = !finished)} />
			{/if}
		</FormSection>
	{/if}

	{#if error && errors.count === 0}
		<div class="mt-4"><Banner tone="danger" icon="alert-triangle">{error}</Banner></div>
	{/if}

	{#snippet footer()}
		<SaveButton busy={busy} onclick={submit} />
		<CancelButton disabled={busy} onclick={onclose} />
	{/snippet}
</FormPage>
