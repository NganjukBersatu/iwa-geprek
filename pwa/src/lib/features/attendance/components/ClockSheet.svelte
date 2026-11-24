<script lang="ts">
	import TextField from '$lib/components/field/TextField.svelte';
	import ToggleSwitch from '$lib/components/field/ToggleSwitch.svelte';
	import Notice from '$lib/components/feedback/Notice.svelte';
	import PhotoSubmitForm from '$lib/components/media/PhotoSubmitForm.svelte';
	import BottomSheet from '$lib/components/sheet/BottomSheet.svelte';
	import { t } from '$lib/text/t';
	import type { AttendanceBranch, ClockKind } from '../models';
	import DistanceNotice from './DistanceNotice.svelte';

	/** Lembar absen: foto dari kamera, dan keterangan wajib bila absen dilakukan di luar lokasi cabang. */
	let {
		kind,
		submitting,
		submitError,
		onSubmit,
		onDismiss,
		notice = null,
		branch = null,
		distance = null,
		locating = false,
		located = false,
		locationProblem = null,
		onRelocate
	}: {
		kind: ClockKind;
		submitting: boolean;
		submitError: string | null;
		onSubmit: (photo: Blob, outside: boolean, note: string) => void;
		onDismiss: () => void;
		notice?: string | null;
		branch?: AttendanceBranch | null;
		distance?: number | null;
		locating?: boolean;
		located?: boolean;
		locationProblem?: string | null;
		onRelocate: () => void;
	} = $props();

	let outside = $state(false);
	let note = $state('');

	const radius = $derived(branch?.radiusMeters ?? null);
	// Sama dengan aturan server: absen di lokasi ditolak bila jaraknya melewati radius.
	const beyondRadius = $derived(distance !== null && radius !== null && distance > radius);
</script>

<BottomSheet title={t(kind === 'in' ? 'attendance_action_in' : 'attendance_action_out')} {onDismiss}>
	{#if notice}<div class="pb-3"><Notice text={notice} /></div>{/if}
	<DistanceNotice {branch} {distance} blocking={beyondRadius && !outside} {locating} {located} {locationProblem} {onRelocate} />
	<PhotoSubmitForm
		submitLabel={t('attendance_submit')}
		onSubmit={(photo) => photo && onSubmit(photo, outside, note)}
		{submitting}
		canSubmit={outside ? note.trim() !== '' : !beyondRadius}
		allowGallery={false}
		error={submitError}
	>
		{#snippet fields()}
			<ToggleSwitch label={t('attendance_outside_toggle')} checked={outside} onchange={(checked) => (outside = checked)} />
			{#if outside}
				<TextField bind:value={note} label={t('attendance_outside_note')} enabled={!submitting} />
			{/if}
		{/snippet}
	</PhotoSubmitForm>
</BottomSheet>
