<script lang="ts">
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import type { AttendanceEdit, AttendanceRecord, AttendanceStatus } from '$lib/api/types';
	import Banner from '$lib/components/card/Banner.svelte';
	import FormPage from '$lib/components/form/FormPage.svelte';
	import FormSection from '$lib/components/form/FormSection.svelte';
	import SelectField from '$lib/components/form/SelectField.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import { formatDate } from '$lib/date/range';
	import { fromWibInput, toWibInput } from '$lib/date/wib';
	import { FieldErrors, focusRefused } from '$lib/components/form/field-errors.svelte';
	import { PAGES, attendancePath } from '$lib/nav/pages';
	import { untrack } from 'svelte';
	import { STATUS_LABELS } from '../labels';
	import { termText } from '$lib/text/terms';
	import { actionText } from '$lib/text/actions';
	import { attendanceListText } from '$lib/text/attendance-list';
	import { format } from '$lib/text/format';

	let {
		record,
		busy,
		error,
		fieldErrors = {},
		onsave,
		onclose
	}: {
		record: AttendanceRecord;
		busy: boolean;
		error: string;
		/** What the server refused, by field name, shown under the field itself. */
		fieldErrors?: Record<string, string>;
		onsave: (changes: AttendanceEdit) => void;
		onclose: () => void;
	} = $props();

	const initial = untrack(() => record);
	const name = initial.name || initial.username;
	const trail = [
		{ label: PAGES.attendance.label, href: PAGES.attendance.path },
		{ label: `${name} · ${formatDate(initial.date)}`, href: attendancePath(initial.id) },
		{ label: actionText.edit }
	];

	let status = $state<string>(initial.status);
	let clockIn = $state(toWibInput(initial.clock_in_at));
	let clockOut = $state(toWibInput(initial.clock_out_at));
	let note = $state(initial.note ?? '');
	const errors = new FieldErrors({ status: termText.status, clock_in_at: attendanceListText.clockIn, clock_out_at: attendanceListText.clockOut, note: termText.note }, () => fieldErrors);

	// A refusal from the server puts the cursor in the first refused box.
	$effect(() => {
		if (Object.keys(fieldErrors).length > 0) void focusRefused();
	});

	const onLeave = $derived(status === 'izin' || status === 'sakit' || status === 'alfa');

	function submit(): void {
		const changes: AttendanceEdit = {};
		if (status !== initial.status) changes.status = status as AttendanceStatus;
		if (!onLeave) {
			if (clockIn !== toWibInput(initial.clock_in_at)) changes.clock_in_at = fromWibInput(clockIn);
			if (clockOut !== toWibInput(initial.clock_out_at)) changes.clock_out_at = fromWibInput(clockOut);
		}
		if (note.trim() !== (initial.note ?? '')) changes.note = note.trim() || null;
		const found: Record<string, string> = {};
		if (Object.keys(changes).length === 0) found.status = attendanceListText.nothingChanged;
		if (!errors.check(found)) return;
		onsave(changes);
	}
</script>

<FormPage title={format(attendanceListText.editAttendanceTitle, { name: name })} description={attendanceListText.formDescription} stacked {trail} {busy} {onclose}>
	<FormSection icon="clock-check" title={attendanceListText.attendance} description={format(attendanceListText.editAttendanceDescription, { date: formatDate(initial.date) })}>
		<div class="grid gap-2 tablet:grid-cols-3">
			<SelectField label={termText.status} bind:value={status} options={Object.entries(STATUS_LABELS).map(([value, label]) => ({ value, label }))} error={errors.get('status')} />
			{#if !onLeave}
				<TextField label={attendanceListText.clockInWib} type="datetime-local" bind:value={clockIn} error={errors.get('clock_in_at')} />
				<TextField label={attendanceListText.clockOutWib} type="datetime-local" bind:value={clockOut} error={errors.get('clock_out_at')} />
			{/if}
		</div>
		{#if onLeave}
			<Banner tone="info" icon="info-circle">{attendanceListText.noTimesNote}</Banner>
		{/if}
	</FormSection>
	<FormSection icon="notes" title={termText.note} description={attendanceListText.noteHint}>
		<TextField label={termText.note} bind:value={note} maxlength={300} error={errors.get('note')} />
	</FormSection>
	{#if error && errors.count === 0}
		<div class="mt-4"><Banner tone="danger" icon="alert-triangle">{error}</Banner></div>
	{/if}

	{#snippet footer()}
		<SaveButton busy={busy} onclick={submit} />
		<CancelButton disabled={busy} onclick={onclose} />
	{/snippet}
</FormPage>
