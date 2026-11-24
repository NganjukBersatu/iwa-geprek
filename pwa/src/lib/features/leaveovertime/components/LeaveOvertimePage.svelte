<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import SegmentedControl from '$lib/components/choice/SegmentedControl.svelte';
	import { DayPlanState } from '$lib/features/dayplan/dayplan.svelte';
	import LeaveSection from '$lib/features/leave/components/LeaveSection.svelte';
	import OvertimeSection from '$lib/features/overtime/components/OvertimeSection.svelte';
	import { t } from '$lib/text/t';

	/** Halaman Izin & Lembur: pilihan Izin atau Lembur di atas, isi bagian terpilih di bawahnya. */
	let { onSessionExpired }: { onSessionExpired: () => void } = $props();

	const dayPlan = new DayPlanState();
	let selectedIndex = $state(0);

	$effect(() => {
		void dayPlan.load(onSessionExpired);
	});

	// Rencana hari dimuat setiap app kembali dari latar belakang, karena lembur terjadwal bisa berubah.
	$effect(() => {
		const reload = () => document.visibilityState === 'visible' && void dayPlan.load(onSessionExpired);
		document.addEventListener('visibilitychange', reload);
		return () => document.removeEventListener('visibilitychange', reload);
	});
</script>

<div class="flex size-full justify-center overflow-y-auto" use:dynamicStyle={{ 'padding-inline': 'var(--page-padding)' }}>
	<div class="flex w-full max-w-[var(--size-content-max)] flex-col gap-3" use:dynamicStyle={{ 'padding-bottom': '24px' }}>
		<SegmentedControl options={[t('leave_overtime_tab_leave'), t('leave_overtime_tab_overtime')]} {selectedIndex} onselect={(index) => (selectedIndex = index)} />
		{#if selectedIndex === 0}
			<LeaveSection {onSessionExpired} />
		{:else}
			<OvertimeSection scheduledOvertime={dayPlan.scheduledOvertime} onRecorded={() => void dayPlan.load(onSessionExpired)} {onSessionExpired} />
		{/if}
	</div>
</div>
