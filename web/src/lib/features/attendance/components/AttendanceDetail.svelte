<script lang="ts">
	import type { UserRecap } from '$lib/api/types';
	import Badge from '$lib/components/card/Badge.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { formatDuration } from '$lib/format/datetime';
	import { STATUS_TONES } from '../../attendance-list/labels';
	import type { AttendanceState } from '../attendance.svelte';
	import { dayColumns, overtimeColumns } from '../columns';
	import { attendanceReportText } from '$lib/text/attendance-report';
	import { format } from '$lib/text/format';

	let { user, attendance }: { user: UserRecap; attendance: AttendanceState } = $props();
</script>

<div class="flex flex-col gap-4">
	{#if user.days.length === 0}
		<p class="py-3 text-center text-xs text-slate-500">{attendanceReportText.noRecordsYet}</p>
	{:else}
		<DataTable sort={attendance.daySort} columns={dayColumns} rows={user.days} rowKey={(row) => `${row.date}|${row.code ?? ''}`}>
			{#snippet cell(row, column)}
				{#if column.key === 'status'}
					<Badge tone={STATUS_TONES[row.status]}>{column.value(row)}</Badge>
					{#if row.automatic}<span class="ml-1 text-xs text-slate-500" title={attendanceReportText.scheduledNoRecord}>{attendanceReportText.automatic}</span>{/if}
				{:else}
					{column.value(row)}
				{/if}
			{/snippet}
		</DataTable>
	{/if}

	<div>
		<p class="mb-2 text-xs font-semibold text-brand">{format(attendanceReportText.overtimeTotalCaption, { duration: formatDuration(user.overtime_minutes) })}</p>
		{#if user.overtime.length === 0}
			<p class="text-xs text-slate-500">{attendanceReportText.noOvertime}</p>
		{:else}
			<DataTable sort={attendance.overtimeSort} columns={overtimeColumns} rows={user.overtime} rowKey={(row) => row.id} />
		{/if}
	</div>
</div>
