<script lang="ts">
	import DropdownField from '$lib/components/field/DropdownField.svelte';
	import SegmentedControl from '$lib/components/choice/SegmentedControl.svelte';
	import OptionalDateTimeField from '$lib/components/field/OptionalDateTimeField.svelte';
	import TextField from '$lib/components/field/TextField.svelte';
	import ToggleSwitch from '$lib/components/field/ToggleSwitch.svelte';
	import type { DateTimeValue } from '$lib/components/field/types';
	import MediaField from '$lib/components/media/MediaField.svelte';
	import type { PickedMedia } from '$lib/components/media/types';
	import FormSheet from '$lib/components/sheet/FormSheet.svelte';
	import { wibIso } from '$lib/format/datetime';
	import { t } from '$lib/text/t';
	import type { NewTask, TaskOptions } from '../tasks.svelte';

	type FormMode = 'self' | 'employee';
	const MODES: FormMode[] = ['self', 'employee'];

	/** Lembar tugas baru: karyawan menulis untuk dirinya sendiri, sedangkan pengelola juga bisa memberi tugas ke karyawan. */
	let {
		options,
		submitting,
		error,
		onSubmit,
		onLoadOptions,
		onDismiss
	}: { options: TaskOptions | null; submitting: boolean; error: string | null; onSubmit: (task: NewTask) => void; onLoadOptions: (outletId: string | null) => void; onDismiss: () => void } = $props();

	let mode = $state<FormMode>('self');
	let outletIndex = $state<number | null>(null);
	let assigneeIndex = $state<number | null>(null);
	let title = $state('');
	let description = $state('');
	let due = $state<DateTimeValue | null>(null);
	let media = $state<PickedMedia[]>([]);
	let done = $state(false);

	const canManage = $derived(options?.canManage === true);
	const outlets = $derived(options?.outlets ?? []);
	const assignees = $derived(options?.assignees ?? []);
	const choosesOutlet = $derived(canManage && mode === 'employee' && outlets.length > 1);
	const finishable = $derived(mode === 'self');
	const valid = $derived(title.trim() !== '' && (mode !== 'employee' || assigneeIndex !== null) && (!choosesOutlet || outletIndex !== null) && (!done || media.length > 0));

	function submit(): void {
		onSubmit({
			title,
			description,
			assigneeId: mode === 'employee' && assigneeIndex !== null ? (assignees[assigneeIndex]?.id ?? null) : null,
			due: due ? wibIso(due.date, due.time) : null,
			complete: done && finishable,
			media
		});
	}
</script>

<FormSheet title={t('tasks_form_title')} submitLabel={t('tasks_form_submit')} onSubmit={submit} {onDismiss} {submitting} canSubmit={valid} {error} loadingOnSubmit>
	{#if canManage}
		<SegmentedControl
			options={[t('tasks_form_mode_self'), t('tasks_form_mode_employee')]}
			selectedIndex={MODES.indexOf(mode)}
			onselect={(index) => {
				mode = MODES[index] ?? 'self';
				done = false;
			}}
		/>
	{/if}
	{#if choosesOutlet}
		<DropdownField
			label={t('tasks_form_outlet')}
			options={[{ key: null, label: t('tasks_form_outlet_pick') }, ...outlets.map((outlet) => ({ key: outlet.id, label: outlet.name }))]}
			selectedKey={outletIndex === null ? null : (outlets[outletIndex]?.id ?? null)}
			onSelect={(key) => {
				const index = outlets.findIndex((outlet) => outlet.id === key);
				outletIndex = index < 0 ? null : index;
				assigneeIndex = null;
				onLoadOptions(key);
			}}
		/>
	{/if}
	{#if mode === 'employee'}
		<DropdownField
			label={t('tasks_form_assignee')}
			options={[{ key: null, label: t('tasks_form_assignee_pick') }, ...assignees.map((person) => ({ key: person.id, label: person.name }))]}
			selectedKey={assigneeIndex === null ? null : (assignees[assigneeIndex]?.id ?? null)}
			onSelect={(key) => {
				const index = assignees.findIndex((person) => person.id === key);
				assigneeIndex = index < 0 ? null : index;
			}}
			searchLabel={t('tasks_filter_person_search')}
		/>
	{/if}
	<TextField bind:value={title} label={t('tasks_form_name')} enabled={!submitting} />
	<TextField bind:value={description} label={t('tasks_form_description')} enabled={!submitting} />
	<OptionalDateTimeField toggleLabel={t('tasks_form_due_toggle')} dateLabel={t('tasks_form_due_date')} timeLabel={t('tasks_form_due_time')} value={due} onchange={(value) => (due = value)} enabled={!submitting} />
	<MediaField items={media} onchange={(items) => (media = items)} enabled={!submitting} />
	{#if finishable}
		<ToggleSwitch label={t('tasks_form_done')} checked={done} onchange={(checked) => (done = checked)} />
	{/if}
</FormSheet>
