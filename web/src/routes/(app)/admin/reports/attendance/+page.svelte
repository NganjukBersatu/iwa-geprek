<script lang="ts">
	import MoreButton from '$lib/components/button/MoreButton.svelte';
	import { attendanceColumns } from '$lib/features/attendance/columns';
	import { AttendanceState } from '$lib/features/attendance/attendance.svelte';
	import AttendanceView from '$lib/features/attendance/components/AttendanceView.svelte';
	import ReportShell from '$lib/features/report/ReportShell.svelte';
	import { pageText } from '$lib/text/pages';

	const attendance = new AttendanceState();
</script>

<ReportShell
	report={attendance}
	title={pageText.attendanceReportTitle}
	description={pageText.attendanceReportDescription}
>
	{#snippet extra()}
		<MoreButton exporter={{ title: pageText.exportTitles.attendance, columns: attendanceColumns, rows: async () => attendance.data?.user ?? [] }} />
	{/snippet}
	{#snippet children(data)}
		<AttendanceView {data} {attendance} />
	{/snippet}
</ReportShell>
