<script lang="ts">
	import SuccessTakeover from '$lib/components/feedback/SuccessTakeover.svelte';
	import { clockOf } from '$lib/format/datetime';
	import { durationLabel } from '$lib/format/labels';
	import { t } from '$lib/text/t';
	import type { ClockCelebration } from '../models';

	/** Perayaan absen: warna teks untuk datang dan warna aksen untuk pulang, sewarna dengan tombol absennya. */
	let { celebration, onDone }: { celebration: ClockCelebration; onDone: () => void } = $props();

	const isIn = $derived(celebration.kind === 'in');
</script>

<SuccessTakeover
	title={t(isIn ? 'attendance_done_in_title' : 'attendance_done_out_title')}
	message={t(isIn ? 'attendance_done_in_message' : 'attendance_done_out_message')}
	countTo={celebration.minutes}
	countLabel={(minutes) => (isIn ? clockOf(minutes) : durationLabel(minutes))}
	actionLabel={t('attendance_done_action')}
	containerColor={isIn ? 'primary' : 'accent'}
	contentColor={isIn ? 'on-primary' : 'content'}
	{onDone}
/>
