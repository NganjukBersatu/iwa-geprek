<script lang="ts">
	import OptionalDateTimeField from '$lib/components/field/OptionalDateTimeField.svelte';
	import TextField from '$lib/components/field/TextField.svelte';
	import type { DateTimeValue } from '$lib/components/field/types';
	import FormSheet from '$lib/components/sheet/FormSheet.svelte';
	import { untrack } from 'svelte';
	import { t } from '$lib/text/t';
	import type { TaskItem } from '../tasks.svelte';

	/** Lembar mengubah judul, keterangan, dan batas waktu tugas yang dibuat sendiri. */
	let {
		task,
		submitting,
		error,
		onSubmit,
		onDismiss
	}: { task: TaskItem; submitting: boolean; error: string | null; onSubmit: (title: string, description: string, due: DateTimeValue | null) => void; onDismiss: () => void } = $props();

	const initial = untrack(() => task);
	let title = $state(initial.title);
	let description = $state(initial.description ?? '');
	let due = $state<DateTimeValue | null>(initial.due ? { date: initial.due.date, time: initial.due.time } : null);
</script>

<FormSheet title={t('tasks_edit_title')} submitLabel={t('tasks_edit_submit')} onSubmit={() => onSubmit(title, description, due)} {onDismiss} {submitting} canSubmit={title.trim() !== ''} {error} loadingOnSubmit>
	<TextField bind:value={title} label={t('tasks_form_name')} enabled={!submitting} />
	<TextField bind:value={description} label={t('tasks_form_description')} enabled={!submitting} />
	<OptionalDateTimeField
		toggleLabel={t('tasks_form_due_toggle')}
		dateLabel={t('tasks_form_due_date')}
		timeLabel={t('tasks_form_due_time')}
		value={due}
		onchange={(value) => (due = value)}
		enabled={!submitting}
		removable={initial.due === null}
	/>
</FormSheet>
