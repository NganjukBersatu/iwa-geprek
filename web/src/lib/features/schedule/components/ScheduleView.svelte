<script lang="ts">
	import { goto } from '$app/navigation';
	import { assignmentNewPath, assignmentPath } from '$lib/nav/pages';
	import { assignableRoles } from '$lib/features/roles/assignable';
	import { formatClockRange } from '$lib/format/datetime';
	import Button from '$lib/components/button/Button.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import BulkActions from '$lib/components/table/BulkActions.svelte';
	import ConfirmDialog from '$lib/components/dialog/ConfirmDialog.svelte';
	import type { ShiftCode } from '$lib/api/types';
	import type { Field } from '$lib/components/form/types';
	import { formatRange } from '$lib/date/range';
	import { Drag, type DragItem, type DropTarget } from '../drag.svelte';
	import type { ScheduleState } from '../schedule.svelte';
	import AssignmentsList from './AssignmentsList.svelte';
	import ShiftCodeBadge from '$lib/components/card/ShiftCodeBadge.svelte';
	import DragGhost from './DragGhost.svelte';
	import ScheduleBoard from './ScheduleBoard.svelte';
	import ScheduleGrid from './ScheduleGrid.svelte';
	import { termText } from '$lib/text/terms';
	import { scheduleText } from '$lib/text/schedule';
	import RichText from '$lib/components/text/RichText.svelte';
	import { format } from '$lib/text/format';

	let { schedule }: { schedule: ScheduleState } = $props();

	const drag = new Drag(
		(item: DragItem, target: DropTarget) => {
			if (item.kind === 'pool') {
				const date = target.kind === 'date' ? target.date : target.kind === 'assignment' ? target.date : null;
				if (date) void goto(assignmentNewPath(date, item.userId));
				return;
			}
			const moved = schedule.items.find((entry) => entry.id === item.id);
			if (!moved) return;
			if (target.kind === 'date') void schedule.move(moved, target.date);
			else if (target.kind === 'pool') schedule.askRelease(moved);
			else if (target.kind === 'assignment') {
				const other = schedule.items.find((entry) => entry.id === target.id);
				if (other && other.id !== moved.id) void schedule.swap(moved, other);
			}
		},
		(item: DragItem) => {
			if (item.kind === 'assignment') void goto(assignmentPath(item.id));
		}
	);

	/** What a code means, written only from what it has: no hours and no category means nothing to add. */
	const note = (code: ShiftCode) => [code.is_day_off ? termText.dayOff : formatClockRange(code.start_clock, code.end_clock), code.category].filter(Boolean).join(' · ');
	const codeOptions = $derived(schedule.workCodes.map((code) => ({ value: code.id, label: code.code })));
	const roleOptions = $derived(assignableRoles(schedule.roles).map((role) => ({ value: role.id, label: role.name })));
	const changeFields = $derived<Field[]>([
		{ key: 'shift_code_id', label: scheduleText.shiftCode, kind: 'select', options: codeOptions },
		{ key: 'role_id', label: scheduleText.dayRole, kind: 'select', options: roleOptions },
		{ key: 'date', label: scheduleText.jumpToDate, kind: 'date' },
		{ key: 'note', label: termText.note }
	]);
</script>

<div class="flex flex-col gap-4">
	<Card>
		<div class="flex flex-wrap items-center justify-between gap-3">
			<p class="text-sm font-semibold text-slate-800">{schedule.range ? formatRange(schedule.range) : '—'}</p>
			<div class="flex items-center gap-2">
				<Button label={scheduleText.boardView} icon="layout-kanban" active={schedule.view === 'board'} onclick={() => (schedule.view = 'board')} />
				<Button label={scheduleText.tableView} icon="table" active={schedule.view === 'grid'} onclick={() => (schedule.view = 'grid')} />
			</div>
		</div>
	</Card>

	{#if schedule.attendanceFailed}
		<Banner tone="warning" icon="alert-triangle" title={scheduleText.attendanceLoadFailedTitle}>{scheduleText.attendanceLoadFailedHint}</Banner>
	{/if}

	{#if schedule.view === 'board'}
		<ScheduleBoard {schedule} {drag} />
	{:else}
		<ScheduleGrid {schedule} />
	{/if}

	<AssignmentsList {schedule} />

	{#if schedule.usedCodes.length > 0}
		<details class="group rounded-xl border border-slate-100 bg-white p-4">
			<summary class="flex cursor-pointer list-none items-center justify-between gap-2 text-sm font-semibold text-slate-800">
				{format(scheduleText.codeLegend, { count: schedule.usedCodes.length })}
				<i class="ti ti-chevron-down text-slate-400 transition-transform group-open:rotate-180" aria-hidden="true"></i>
			</summary>
			<div class="mt-3 flex flex-col gap-4">
				{#each schedule.legend as group (group.outletId)}
					<section>
						<h4 class="text-xs font-semibold text-slate-500">{group.name}</h4>
						<ul class="mt-2 grid gap-2 tablet:grid-cols-2 laptop:grid-cols-3">
							{#each group.codes as code (code.id)}
								<li class="flex items-center gap-2 text-xs text-slate-500">
									<ShiftCodeBadge {code} />
									{#if note(code)}<span class="text-slate-600">{note(code)}</span>{/if}
								</li>
							{/each}
						</ul>
					</section>
				{/each}
			</div>
		</details>
	{/if}
</div>

<DragGhost {drag} />

<ConfirmDialog open={schedule.releasing !== null} title={scheduleText.unassignTitle} confirmLabel="Lepas" danger busy={schedule.working} onconfirm={() => void schedule.confirmRelease()} oncancel={() => (schedule.releasing = null)}>
	<RichText template={scheduleText.unassignNote} values={{ name: schedule.releasing?.user_username ?? '', date: schedule.releasing?.date ?? '' }} />
</ConfirmDialog>

<ConfirmDialog open={schedule.releasingOff !== null} title={scheduleText.unassignDayOffTitle} confirmLabel="Lepas libur" danger busy={schedule.working} onconfirm={() => void schedule.confirmReleaseOff()} oncancel={() => (schedule.releasingOff = null)}>
	<RichText template={scheduleText.dayOffUnassignNote} values={{ name: schedule.releasingOff?.user_username ?? '', date: schedule.releasingOff?.date ?? '' }} />
</ConfirmDialog>

{#if schedule.canArrange}
	<BulkActions
		selection={schedule.selection}
		noun="jadwal"
		bind:removing={schedule.bulkRemoveOpen}
		bind:changing={schedule.changeOpen}
		fields={changeFields}
		onchange={(changes) => void schedule.changeSelected(changes)}
		busy={schedule.busy}
		error={schedule.actionError}
		onremove={() => void schedule.removeSelected()}
		oncancel={() => schedule.closeDialogs()}
	>
		{scheduleText.bulkRemoveNote}
	</BulkActions>
{/if}
