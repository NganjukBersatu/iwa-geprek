<script lang="ts">
	import SourceButton from '$lib/components/button/SourceButton.svelte';
	import ChoiceGroup from '$lib/components/choice/ChoiceGroup.svelte';
	import DateField from '$lib/components/field/DateField.svelte';
	import TextField from '$lib/components/field/TextField.svelte';
	import Notice from '$lib/components/feedback/Notice.svelte';
	import PhotoSubmitForm from '$lib/components/media/PhotoSubmitForm.svelte';
	import BottomSheet from '$lib/components/sheet/BottomSheet.svelte';
	import { todayWib } from '$lib/format/datetime';
	import { pickPdf, type PickedPdf } from '$lib/platform/pdf';
	import { t } from '$lib/text/t';
	import { ServerClock } from '$lib/time/server-clock';
	import type { LeaveAttachment, LeaveForm, LeaveType } from '../leave.svelte';

	const TYPES: LeaveType[] = ['izin', 'sakit'];

	/** Lembar mengajukan izin atau sakit; lampiran berupa foto atau PDF, atau bila tanpa lampiran, tautan. */
	let {
		submitting,
		error,
		onSubmit,
		onDismiss
	}: { submitting: boolean; error: string | null; onSubmit: (form: LeaveForm, attachment: LeaveAttachment | null) => void; onDismiss: () => void } = $props();

	const today = todayWib(ServerClock.nowEpochSeconds());

	let type = $state<LeaveType>('izin');
	let start = $state(today);
	let end = $state(today);
	let reason = $state('');
	let link = $state('');
	let pdf = $state<PickedPdf | null>(null);

	const datesValid = $derived(end >= start);
	const localError = $derived(datesValid ? null : t('leave_date_invalid'));

	async function togglePdf(): Promise<void> {
		if (pdf) pdf = null;
		else pdf = (await pickPdf()) ?? null;
	}

	function submit(photo: Blob | null): void {
		// PDF yang dipilih menggantikan foto sebagai lampiran.
		const attachment: LeaveAttachment | null = pdf ? { blob: pdf.blob, fileName: 'lampiran.pdf' } : photo ? { blob: photo, fileName: 'lampiran.jpg' } : null;
		onSubmit({ type, startDate: start, endDate: end, reason, link }, attachment);
	}
</script>

<BottomSheet title={t('leave_action')} {onDismiss}>
	<PhotoSubmitForm
		submitLabel={t('leave_submit')}
		onSubmit={submit}
		{submitting}
		canSubmit={datesValid && reason.trim() !== ''}
		photoRequired={link.trim() === '' && pdf === null}
		error={localError ?? error}
	>
		{#snippet fields()}
			<ChoiceGroup label={t('leave_type')} options={TYPES.map((item) => (item === 'sakit' ? t('leave_type_sick') : t('leave_type_permit')))} selectedIndex={TYPES.indexOf(type)} onselect={(index) => (type = TYPES[index] ?? 'izin')} />
			<DateField
				label={t('leave_start')}
				value={start}
				{today}
				enabled={!submitting}
				onchange={(date) => {
					start = date;
					if (end < date) end = date;
				}}
			/>
			<DateField label={t('leave_end')} value={end} {today} enabled={!submitting} onchange={(date) => (end = date)} />
			<TextField bind:value={reason} label={t('leave_reason')} enabled={!submitting} />
			<TextField bind:value={link} label={t('leave_link')} enabled={!submitting} />
			<SourceButton label={t(pdf === null ? 'leave_pdf_pick' : 'leave_pdf_remove')} icon="FileText" tone="library" enabled={!submitting} onclick={() => void togglePdf()} />
			{#if pdf}<Notice text={t('leave_pdf_selected', pdf.name)} />{/if}
		{/snippet}
	</PhotoSubmitForm>
</BottomSheet>
