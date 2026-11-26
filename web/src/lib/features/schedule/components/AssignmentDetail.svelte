<script lang="ts">
	import { untrack } from 'svelte';
	import { api } from '$lib/api';
	import type { Assignment, AttendanceRecord, AttendanceStatus, Role, ShiftCode } from '$lib/api/types';
	import { access } from '$lib/auth/access.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import ConfirmDialog from '$lib/components/dialog/ConfirmDialog.svelte';
	import FigureList from '$lib/components/card/FigureList.svelte';
	import { toast } from '$lib/components/feedback/toast.svelte';
	import { dayLabel, formatDate } from '$lib/date/range';
	import { EMPTY_VALUE } from '$lib/format/currency';
	import { formatClockRange, formatTime } from '$lib/format/datetime';
	import { PAGES } from '$lib/nav/pages';
	import { recordText } from '$lib/text/record-detail';
	import { ServerClock } from '$lib/time/server-clock';
	import RecordDetailView from '../../record-detail/components/RecordDetailView.svelte';
	import { RecordDetailState } from '../../record-detail/record-detail.svelte';
	import AttendanceMark from './AttendanceMark.svelte';
	import ShiftCodeBadge from '$lib/components/card/ShiftCodeBadge.svelte';
	import AssignmentForm, { type AssignmentEdit } from './AssignmentForm.svelte';
	import { termText } from '$lib/text/terms';
	import { scheduleText } from '$lib/text/schedule';
	import { shiftCodeText } from '$lib/text/shift-codes';
	import { format } from '$lib/text/format';
	import RichText from '$lib/components/text/RichText.svelte';

	/** What the page reads besides the assignment: the codes, the roles, and the attendance of that day. */
	type DetailContext = { codes: ShiftCode[]; roles: Role[]; attendance: AttendanceRecord[]; attendanceFailed: boolean };

	const STATUSES = [
		{ status: 'hadir', label: scheduleText.markPresent, icon: 'login', variant: 'successSoft' },
		{ status: 'izin', label: scheduleText.markLeave, icon: 'file-text', variant: 'infoSoft' },
		{ status: 'sakit', label: termText.sick, icon: 'first-aid-kit', variant: 'warningSoft' },
		{ status: 'alfa', label: termText.absent, icon: 'user-x', variant: 'dangerSoft' }
	] as const;

	let { id }: { id: string } = $props();

	const canArrange = access.allows('arrange_schedule');
	const canMark = access.allows('mark_attendance');

	/** The record of this assignment: linked to it, or else the one of the same person, day and code. */
	function recordOf(assignment: Assignment, context: DetailContext | null): AttendanceRecord | undefined {
		if (!context) return undefined;
		const code = context.codes.find((item) => item.id === assignment.shift_code_id)?.code;
		return (
			context.attendance.find((record) => record.schedule_id === assignment.id) ??
			(code ? context.attendance.find((record) => record.user_id === assignment.user_id && record.date === assignment.date && record.shift_code === code) : undefined)
		);
	}

	const detail = new RecordDetailState<Assignment, AssignmentEdit, DetailContext>(untrack(() => id), {
		load: (assignmentId) => api.schedule.assignments.get(assignmentId),
		context: async () => {
			const assignment = await api.schedule.assignments.get(untrack(() => id));
			const [codes, roles, attendance] = await Promise.all([
				api.schedule.codes(),
				api.roles.list(),
				canMark
					? api.attendance.range({ start: assignment.date, end: assignment.date, user_id: assignment.user_id }).then(
							(records) => ({ records, failed: false }),
							() => ({ records: [] as AttendanceRecord[], failed: true })
						)
					: Promise.resolve({ records: [] as AttendanceRecord[], failed: false })
			]);
			return { codes, roles, attendance: attendance.records, attendanceFailed: attendance.failed };
		},
		update: canArrange
			? async (assignment, { changes, times }) => {
					const record = recordOf(assignment, detail.context);
					if (Object.keys(changes).length > 0) await api.schedule.assignments.update(assignment.id, changes);
					if (times) {
						if (record) await api.attendance.edit(record.id, { clock_in_at: times.clockIn, clock_out_at: times.clockOut });
						// Kehadiran baru mengikuti tanggal dan kode shift yang baru saja diubah, bukan nilai lamanya.
						else
							await api.attendance.mark({
								user_id: assignment.user_id,
								date: changes.date ?? assignment.date,
								shift_code_id: changes.shift_code_id !== undefined ? changes.shift_code_id : assignment.shift_code_id,
								status: 'hadir',
								schedule_id: assignment.id,
								clock_in_at: times.clockIn,
								clock_out_at: times.clockOut
							});
					}
					return api.schedule.assignments.get(assignment.id);
				}
			: undefined,
		remove: canArrange ? (assignment) => api.schedule.assignments.remove(assignment.id) : undefined,
		name: (assignment) => assignment.user_username,
		text: recordText('jadwal', PAGES.schedule.label)
	});

	/** Runs one attendance action, then reads the page again so the record shown is the stored one. */
	async function act(work: () => Promise<unknown>, success: string, failure: string): Promise<void> {
		if (!(await detail.run(work, failure))) return;
		toast.show(success);
		await detail.refresh();
	}

	const mark = (assignment: Assignment, status: AttendanceStatus) =>
		act(
			() => api.attendance.mark({ user_id: assignment.user_id, date: assignment.date, shift_code_id: assignment.shift_code_id, status, schedule_id: assignment.id }),
			scheduleText.attendanceRecorded,
			scheduleText.attendanceRecordFailed
		);
	/** Alfa is the one status that is hard to take back, so it is asked for twice; the other statuses apply at once. */
	let confirmingAbsent = $state(false);
	const choose = (assignment: Assignment, status: AttendanceStatus) => (status === 'alfa' ? void (confirmingAbsent = true) : void mark(assignment, status));
	const clockOut = (record: AttendanceRecord) => act(() => api.attendance.edit(record.id, { clock_out_at: ServerClock.now().toISOString() }), scheduleText.clockOutRecorded, scheduleText.clockOutRecordFailed);
	const removeRecord = (record: AttendanceRecord) => act(() => api.attendance.remove(record.id), scheduleText.attendanceRemoved, scheduleText.attendanceRemoveFailed);

	const codeOf = (assignment: Assignment, context: DetailContext | null) => context?.codes.find((code) => code.id === assignment.shift_code_id);
</script>

<RecordDetailView
	{detail}
	back={PAGES.schedule}
	trail={(assignment) => [{ label: PAGES.schedule.label, href: PAGES.schedule.path }, { label: `${assignment.user_username} · ${formatDate(assignment.date)}` }]}
	tables={['schedules', 'attendance_records', 'shift_codes']}
	title={(assignment) => assignment.user_username}
	description={(assignment) => formatDate(assignment.date)}
>
	{#snippet body(assignment, context)}
		{@const code = codeOf(assignment, context)}
		{@const record = recordOf(assignment, context)}
		{@const hours = code?.is_day_off ? termText.dayOff : code ? formatClockRange(code.start_clock, code.end_clock) : ''}
		<Card flush>
			<div class="flex flex-col gap-4 border-b border-slate-100 p-4 tablet:p-5">
				<div class="flex items-center justify-between gap-3">
					<div>
						<p class="text-2xl font-semibold text-brand-ink">{hours || shiftCodeText.noWorkHours}</p>
						<p class="mt-0.5 text-xs text-slate-500">{dayLabel(assignment.date).weekday}, {formatDate(assignment.date)}</p>
					</div>
					<ShiftCodeBadge {code} />
				</div>
				<div class="border-t border-slate-100 pt-4">
					<FigureList
						figures={[
							{ label: termText.employee, value: assignment.user_username },
							{ label: scheduleText.dayRole, value: assignment.role_name ?? EMPTY_VALUE },
							{ label: termText.note, value: assignment.note ?? EMPTY_VALUE }
						]}
					/>
				</div>
			</div>
			{#if canMark}
				<div class="flex flex-col gap-4 p-4 tablet:p-5">
					<div class="flex items-center justify-between gap-2">
						<h2 class="font-semibold text-slate-800">{scheduleText.attendance}</h2>
						{#if record}<AttendanceMark {record} />{:else}<span class="text-xs text-slate-500">{scheduleText.notRecorded}</span>{/if}
					</div>
					<FigureList
						figures={[
							{ label: scheduleText.clockIn, value: record?.clock_in_at ? formatTime(record.clock_in_at) : EMPTY_VALUE },
							{ label: scheduleText.clockOut, value: record?.clock_out_at ? formatTime(record.clock_out_at) : EMPTY_VALUE }
						]}
					/>
					{#if context?.attendanceFailed}
						<Banner tone="warning" icon="alert-triangle">{scheduleText.attendanceUnavailableWarning}</Banner>
					{:else}
						<div class="flex flex-wrap gap-2 border-t border-slate-100 pt-4">
							{#each STATUSES as option (option.status)}
								<Button label={option.label} icon={option.icon} variant={option.variant} disabled={detail.busy} onclick={() => choose(assignment, option.status)} />
							{/each}
						</div>
						{#if record}
							<div class="flex flex-wrap gap-2">
								{#if record.clock_in_at && !record.clock_out_at}
									<Button label={scheduleText.clockOutNow} icon="logout" disabled={detail.busy} onclick={() => void clockOut(record)} />
								{/if}
								<Button label={scheduleText.removeRecord} icon="trash" variant="dangerSoft" disabled={detail.busy} onclick={() => void removeRecord(record)} />
							</div>
						{/if}
					{/if}
				</div>
			{/if}
		</Card>
		<ConfirmDialog
			open={confirmingAbsent}
			title={format(scheduleText.markAbsentTitle, { name: assignment.user_username })}
			confirmLabel={scheduleText.markAbsentConfirm}
			danger
			busy={detail.busy}
			onconfirm={() => void mark(assignment, 'alfa').then(() => (confirmingAbsent = false))}
			oncancel={() => (confirmingAbsent = false)}
		>
			{format(scheduleText.markAbsentNote, { name: assignment.user_username, hours: hours || EMPTY_VALUE, date: formatDate(assignment.date) })}
		</ConfirmDialog>
	{/snippet}
	{#snippet form(props)}
		<AssignmentForm
			assignment={props.record}
			codes={props.context?.codes ?? []}
			roles={props.context?.roles ?? []}
			record={recordOf(props.record, props.context) ?? null}
			canCorrect={canMark && !(props.context?.attendanceFailed ?? true)}
			busy={props.busy}
			error={props.error}
			fieldErrors={props.fieldErrors}
			onsave={(value) => props.onsave(value as AssignmentEdit)}
			onclose={props.onclose}
		/>
	{/snippet}
	{#snippet removeNote(assignment)}
		<RichText template={scheduleText.unassignNote} values={{ name: assignment.user_username, date: formatDate(assignment.date) }} />
	{/snippet}
</RecordDetailView>
