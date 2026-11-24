<script lang="ts">
	import DateField from '$lib/components/field/DateField.svelte';
	import TextField from '$lib/components/field/TextField.svelte';
	import TimeField from '$lib/components/field/TimeField.svelte';
	import FormSheet from '$lib/components/sheet/FormSheet.svelte';
	import { stampAt, todayWib } from '$lib/format/datetime';
	import { t } from '$lib/text/t';
	import { ServerClock } from '$lib/time/server-clock';
	import type { OvertimeRequest } from '../overtime.svelte';

	const DEFAULT_SPAN_SECONDS = 3600;

	/** Lembar mencatat lembur di luar jadwal: mulai dan selesai bertanggal, serta alasan yang wajib diisi. */
	let { submitting, error, onSubmit, onDismiss }: { submitting: boolean; error: string | null; onSubmit: (request: OvertimeRequest) => void; onDismiss: () => void } = $props();

	const now = ServerClock.nowEpochSeconds();
	const today = todayWib(now);
	const begin = stampAt(now);
	const finish = stampAt(now + DEFAULT_SPAN_SECONDS);

	let startDate = $state(begin.date);
	let startTime = $state(begin.time);
	let endDate = $state(finish.date);
	let endTime = $state(finish.time);
	let note = $state('');

	const orderValid = $derived(`${endDate} ${endTime}` > `${startDate} ${startTime}`);
</script>

<FormSheet
	title={t('overtime_form_title')}
	submitLabel={t('overtime_form_submit')}
	onSubmit={() => onSubmit({ startDate, startTime, endDate, endTime, note })}
	{onDismiss}
	{submitting}
	canSubmit={orderValid && note.trim() !== ''}
	error={orderValid ? error : t('overtime_form_order_invalid')}
	loadingOnSubmit
>
	<DateField label={t('overtime_form_start_date')} value={startDate} {today} enabled={!submitting} onchange={(date) => (startDate = date)} />
	<TimeField label={t('overtime_form_start_time')} value={startTime} enabled={!submitting} onchange={(time) => (startTime = time)} />
	<DateField label={t('overtime_form_end_date')} value={endDate} {today} enabled={!submitting} onchange={(date) => (endDate = date)} />
	<TimeField label={t('overtime_form_end_time')} value={endTime} enabled={!submitting} onchange={(time) => (endTime = time)} />
	<TextField bind:value={note} label={t('overtime_form_note')} enabled={!submitting} />
</FormSheet>
