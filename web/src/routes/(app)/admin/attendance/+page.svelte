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
	import { page } from '$app/state';
	import { LEAVE_TAB } from '$lib/nav/pages';

	const attendance = new AttendanceListState();
	const leave = new LeaveRequestsState();
	leave.onchanged = () => void attendance.refresh();

	let tab = $state(page.url.searchParams.get('tab') === LEAVE_TAB ? LEAVE_TAB : 'absensi');

	const tabs = $derived([
		{ key: 'absensi', label: pageText.attendance, count: attendance.loaded ? attendance.total : undefined },
		{ key: LEAVE_TAB, label: pageText.leaveRequests, count: leave.loaded ? leave.pending : undefined }
	]);

	whenChanged(() => leave.query, () => void leave.queryChanged());
	onMount(() => live.on(leave.tables, () => void leave.refresh()));
</script>

<ManageShell
	manage={attendance}
	filters={tab === LEAVE_TAB ? leave.filters : attendance.filters}
	title={pageText.attendanceListTitle}
	description={pageText.attendanceListDescription}
	loadingText={pageText.loadingAttendance}
>
	{#snippet children()}
		<Tabs {tabs} label={pageText.pageContents} bind:value={tab} class="-mt-2" />
		{#key tab}
			<div in:enter>
				{#if tab === LEAVE_TAB}
					<LeaveRequestsPanel {leave} />
				{:else}
					<AttendanceView {attendance} />
				{/if}
			</div>
		{/key}
	{/snippet}
</ManageShell>
