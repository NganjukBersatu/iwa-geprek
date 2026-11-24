<script lang="ts" module>
	import type { AssignmentUpdate } from '$lib/api/types';

	/** What a new assignment or a day off is made from. */
	export type AssignmentDraft = { userId: string; date: string; codeId: string; roleId: string | null };
	/** What an edit sends: the schedule changes, and the corrected clock times when they were touched. */
	export type AssignmentEdit = { changes: AssignmentUpdate; times: { clockIn: string | null; clockOut: string | null } | null };
</script>

<script lang="ts">
	import { assignableRoles } from '$lib/features/roles/assignable';
	import type { Assignment, AttendanceRecord, PoolUser, Role, ShiftCode } from '$lib/api/types';
	import Banner from '$lib/components/card/Banner.svelte';
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import FormPage from '$lib/components/form/FormPage.svelte';
	import FormSection from '$lib/components/form/FormSection.svelte';
	import SelectField from '$lib/components/form/SelectField.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import { FieldErrors, focusRefused } from '$lib/components/form/field-errors.svelte';
	import { formatDate } from '$lib/date/range';
	import { fromWibInput, toWibInput } from '$lib/date/wib';
	import { formatClockRange } from '$lib/format/datetime';
	import { PAGES, assignmentPath } from '$lib/nav/pages';
	import { untrack } from 'svelte';
	import { termText } from '$lib/text/terms';
	import { actionText } from '$lib/text/actions';
	import { scheduleText } from '$lib/text/schedule';
	import { format } from '$lib/text/format';

	let {
		assignment,
		pool = [],
		codes,
		roles,
		record = null,
		canCorrect = false,
		startDate = '',
		startUser = '',
		busy,
		error,
		fieldErrors = {},
		onsave,
		onclose
	}: {
		assignment: Assignment | null;
		/** The people a new assignment may name; unused when editing. */
		pool?: PoolUser[];
		codes: ShiftCode[];
		roles: Role[];
		/** The attendance of this assignment, when the person may correct it. */
		record?: AttendanceRecord | null;
		canCorrect?: boolean;
		startDate?: string;
		startUser?: string;
		busy: boolean;
		error: string;
		/** What the server refused, by field name, shown under the field itself. */
		fieldErrors?: Record<string, string>;
		onsave: (value: AssignmentDraft | AssignmentEdit) => void;
		onclose: () => void;
	} = $props();

	const current = untrack(() => assignment);
	const trail = [
		{ label: PAGES.schedule.label, href: PAGES.schedule.path },
		...(current ? [{ label: `${current.user_username} · ${formatDate(current.date)}`, href: assignmentPath(current.id) }, { label: actionText.edit }] : [{ label: scheduleText.addAssignment }])
	];

	let userId = $state(untrack(() => startUser));
	let date = $state(current?.date ?? untrack(() => startDate));
	let codeId = $state(current?.shift_code_id ?? '');
	let roleId = $state(current?.role_id ?? '');
	let clockIn = $state(toWibInput(untrack(() => record?.clock_in_at ?? null)));
	let clockOut = $state(toWibInput(untrack(() => record?.clock_out_at ?? null)));
	const errors = new FieldErrors(
		{ user_id: termText.employee, date: termText.date, shift_code_id: scheduleText.shiftCode, role_id: scheduleText.dayRole, clock_in_at: scheduleText.clockIn, clock_out_at: scheduleText.clockOut },
		() => fieldErrors
	);

	// A refusal from the server puts the cursor in the first refused box.
	$effect(() => {
		if (Object.keys(fieldErrors).length > 0) void focusRefused();
	});

	const choices = $derived(current ? codes.filter((code) => !code.is_day_off) : codes);
	const dayOff = $derived(codes.find((code) => code.id === codeId)?.is_day_off ?? false);
	const codeOptions = $derived(
		choices.map((code) => ({ value: code.id, label: `${code.code}${code.is_day_off ? ' (libur)' : code.start_clock && code.end_clock ? ` · ${formatClockRange(code.start_clock, code.end_clock)}` : ''}` }))
	);
	const roleOptions = $derived(assignableRoles(roles).map((role) => ({ value: role.id, label: role.name })));

	function submit(): void {
		const found: Record<string, string> = {};
		if (!current && !userId) found.user_id = scheduleText.employeeRequired;
		if (!date) found.date = scheduleText.dateRequired;
		if (!codeId) found.shift_code_id = scheduleText.shiftCodeRequired;
		if (!errors.check(found)) return;
		if (!current) return onsave({ userId, date, codeId, roleId: dayOff || !roleId ? null : roleId });
		const changes: AssignmentUpdate = {};
		if (codeId !== (current.shift_code_id ?? '')) changes.shift_code_id = codeId || null;
		if (roleId !== (current.role_id ?? '')) changes.role_id = roleId || null;
		if (date !== current.date) changes.date = date;
		const originalIn = toWibInput(record?.clock_in_at ?? null);
		const originalOut = toWibInput(record?.clock_out_at ?? null);
		const times = canCorrect && (clockIn !== originalIn || clockOut !== originalOut) ? { clockIn: fromWibInput(clockIn), clockOut: fromWibInput(clockOut) } : null;
		if (Object.keys(changes).length === 0 && !times) {
			errors.check({ shift_code_id: scheduleText.nothingChanged });
			return;
		}
		onsave({ changes, times });
	}
</script>

<FormPage
	title={current ? format(scheduleText.editAssignmentTitle, { name: current.user_username }) : scheduleText.addAssignment}
	description={current ? formatDate(current.date) : scheduleText.formDescription}
	stacked
	{trail}
	{busy}
	{onclose}
>
	<FormSection icon="calendar-event" title={termText.schedule} description={scheduleText.sectionDescription}>
		<div class="grid gap-2 tablet:grid-cols-3">
			{#if !current}
				<SelectField label={termText.employee} bind:value={userId} empty={scheduleText.chooseEmployee} required options={pool.map((person) => ({ value: person.id, label: person.name || person.username }))} error={errors.get('user_id')} />
			{/if}
			<TextField label={termText.date} type="date" bind:value={date} required error={errors.get('date')} />
			<SelectField label={scheduleText.shiftCode} bind:value={codeId} empty={current ? '— tanpa kode —' : '— pilih kode —'} required options={codeOptions} error={errors.get('shift_code_id')} />
			{#if !dayOff}
				<SelectField label={scheduleText.dayRoleOptional} bind:value={roleId} empty={scheduleText.noRole} options={roleOptions} hint={scheduleText.dayRoleHint} error={errors.get('role_id')} />
			{/if}
		</div>
	</FormSection>
	{#if current && canCorrect}
		<FormSection icon="clock-edit" title={scheduleText.correctTimes} description={scheduleText.correctTimesDescription}>
			<div class="grid gap-2 tablet:grid-cols-2">
				<TextField label={scheduleText.clockInWib} type="datetime-local" bind:value={clockIn} error={errors.get('clock_in_at')} />
				<TextField label={scheduleText.clockOutWib} type="datetime-local" bind:value={clockOut} error={errors.get('clock_out_at')} />
			</div>
		</FormSection>
	{/if}
	{#if error && errors.count === 0}
		<div class="mt-4"><Banner tone="danger" icon="alert-triangle">{error}</Banner></div>
	{/if}

	{#snippet footer()}
		<SaveButton busy={busy} onclick={submit} />
		<CancelButton disabled={busy} onclick={onclose} />
	{/snippet}
</FormPage>
