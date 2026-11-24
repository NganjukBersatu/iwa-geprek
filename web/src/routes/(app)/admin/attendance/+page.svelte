<script lang="ts">
	import { whenChanged } from '$lib/stores/when-changed.svelte';
	import { onMount } from 'svelte';
	import Tabs from '$lib/components/tabs/Tabs.svelte';
	import AttendanceView from '$lib/features/attendance-list/components/AttendanceView.svelte';
	import { AttendanceListState } from '$lib/features/attendance-list/attendance-list.svelte';
	import LeaveRequestsPanel from '$lib/features/leave-requests/components/LeaveRequestsPanel.svelte';
	import { LeaveRequestsState } from '$lib/features/leave-requests/leave-requests.svelte';
	import ManageShell from '$lib/features/manage/ManageShell.svelte';
	import { live } from '$lib/live/live';
	import { enter } from '$lib/motion/transitions';
	import { pageText } from '$lib/text/pages';

	const attendance = new AttendanceListState();
	const leave = new LeaveRequestsState();
	leave.onchanged = () => void attendance.refresh();

	let tab = $state('absensi');

	const tabs = $derived([
		{ key: 'absensi', label: pageText.attendance, count: attendance.loaded ? attendance.total : undefined },
		{ key: 'izin', label: pageText.leaveRequests, count: leave.loaded ? leave.pending : undefined }
	]);

	whenChanged(() => leave.query, () => void leave.queryChanged());
	onMount(() => live.on(leave.tables, () => void leave.refresh()));
</script>

<ManageShell
	manage={attendance}
	filters={tab === 'izin' ? leave.filters : attendance.filters}
	title={pageText.attendanceListTitle}
	description={pageText.attendanceListDescription}
	loadingText="Memuat absensi..."
>
	{#snippet children()}
		<Tabs {tabs} label={pageText.pageContents} bind:value={tab} class="-mt-2" />
		{#key tab}
			<div in:enter>
				{#if tab === 'izin'}
					<LeaveRequestsPanel {leave} />
				{:else}
					<AttendanceView {attendance} />
				{/if}
			</div>
		{/key}
	{/snippet}
</ManageShell>
