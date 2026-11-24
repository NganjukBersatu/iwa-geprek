<script lang="ts">
	import { goto } from '$app/navigation';
	import { assignmentNewPath, assignmentPath } from '$lib/nav/pages';
	import IconButton from '$lib/components/button/IconButton.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import MatrixTable, { type MatrixColumn } from '$lib/components/table/MatrixTable.svelte';
	import { dayLabel, todayIso } from '$lib/date/range';
	import type { ScheduleState } from '../schedule.svelte';
	import AttendanceMark from './AttendanceMark.svelte';
	import ShiftCodeBadge from '$lib/components/card/ShiftCodeBadge.svelte';
	import { termText } from '$lib/text/terms';
	import { scheduleText } from '$lib/text/schedule';
	import { format } from '$lib/text/format';

	let { schedule }: { schedule: ScheduleState } = $props();

	const today = todayIso();
	const columns = $derived<MatrixColumn[]>(
		schedule.dates.map((date) => {
			const label = dayLabel(date);
			return { key: date, label: `${label.weekday} ${label.day}`, head: `min-w-24 text-center ${date === today ? 'bg-brand text-white' : ''}` };
		})
	);
</script>

<Card flush>
	{#if schedule.people.length === 0}
		<Notice text={scheduleText.noScheduledEmployees} />
	{:else}
		<MatrixTable leadLabel="Karyawan" {columns} rows={schedule.people} rowKey={([userId]) => userId}>
			{#snippet lead([, username])}
				<span class="font-semibold text-slate-800">{username}</span>
			{/snippet}
			{#snippet cell([userId, username], column)}
				{@const date = column.key}
				{@const mine = schedule.itemsOn(date).filter((item) => item.user_id === userId)}
				{@const off = schedule.daysOffOn(date).find((item) => item.user_id === userId)}
				<span class="flex flex-col items-center gap-0.5">
					{#each mine as item (item.id)}
						<button type="button" onclick={() => void goto(assignmentPath(item.id))} class="flex w-full flex-col items-center gap-0.5 rounded-lg px-1 py-0.5 hover:bg-brand-page" aria-label={format(scheduleText.scheduleOfPersonDate, { name: username, date: date })}>
							<ShiftCodeBadge code={schedule.codeOf(item.shift_code_id)} />
							<AttendanceMark record={schedule.attendanceFor(item)} />
						</button>
					{/each}
					{#if off}
						<span class="text-xs text-slate-500" title={termText.dayOff}>{scheduleText.dayOffLower}</span>
					{:else if mine.length === 0 && schedule.canArrange}
						<IconButton size="sm" icon="plus" label={format(scheduleText.assignPersonDate, { name: username, date: date })} onclick={() => void goto(assignmentNewPath(date, userId))} />
					{/if}
				</span>
			{/snippet}
		</MatrixTable>
	{/if}
</Card>
