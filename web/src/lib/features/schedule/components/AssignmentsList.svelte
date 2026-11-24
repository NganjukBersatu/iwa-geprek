<script lang="ts">
	import { goto } from '$app/navigation';
	import { assignmentPath } from '$lib/nav/pages';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import Pager from '$lib/components/pager/Pager.svelte';
	import { pageOf } from '$lib/components/pager/page-of';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { assignmentColumns } from '../columns';
	import type { ScheduleState } from '../schedule.svelte';
	import AttendanceMark from './AttendanceMark.svelte';
	import ShiftCodeBadge from '$lib/components/card/ShiftCodeBadge.svelte';
	import { scheduleText } from '$lib/text/schedule';

	let { schedule }: { schedule: ScheduleState } = $props();

	const shown = $derived(pageOf(schedule.items, schedule.page));
	const columns = $derived(assignmentColumns(schedule.codeOf));
</script>

<Card flush>
	<CardHeader divided title={scheduleText.listTitle} description={scheduleText.listDescription} />
	{#if schedule.items.length === 0}
		<Notice text={scheduleText.noAssignments} />
	{:else}
		<DataTable sort={schedule.sort} {columns} rows={shown.rows} rowKey={(row) => row.id} loading={schedule.loading} selection={schedule.canArrange ? schedule.selection : undefined} onopen={(row) => void goto(assignmentPath(row.id))}>
			{#snippet cell(row, column)}
				{#if column.key === 'kode'}
					<ShiftCodeBadge code={schedule.codeOf(row.shift_code_id)} showTime />
				{:else if column.key === 'kehadiran'}
					<AttendanceMark record={schedule.attendanceFor(row)} />
				{:else}
					{column.value(row)}
				{/if}
			{/snippet}
		</DataTable>
		<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
			<Pager page={shown.page} total={schedule.items.length} unit="jadwal" disabled={schedule.loading} onchange={(next) => (schedule.page = next)} />
		</div>
	{/if}
</Card>
