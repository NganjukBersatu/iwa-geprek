<script lang="ts">
	import { page } from '$app/state';
	import { api } from '$lib/api';
	import type { Assignment, PoolUser, Role, ShiftCode } from '$lib/api/types';
	import { PAGES, assignmentPath } from '$lib/nav/pages';
	import { createText } from '$lib/text/record-detail';
	import RecordCreateView from '../../record-detail/components/RecordCreateView.svelte';
	import { RecordCreateState } from '../../record-detail/record-create.svelte';
	import { SCHEDULE_DATE_PARAM, SCHEDULE_USER_PARAM } from '../params';
	import AssignmentForm, { type AssignmentDraft } from './AssignmentForm.svelte';
	import { termText } from '$lib/text/terms';
	import { scheduleText } from '$lib/text/schedule';
	import { format } from '$lib/text/format';

	type CreateContext = { pool: PoolUser[]; codes: ShiftCode[]; roles: Role[] };
	/** A work shift opens its own page; a day off has none, so the board is shown again. */
	type Created = { assignment: Assignment | null; user: string };

	const startDate = page.url.searchParams.get(SCHEDULE_DATE_PARAM) ?? '';
	const startUser = page.url.searchParams.get(SCHEDULE_USER_PARAM) ?? '';

	let context: CreateContext = { pool: [], codes: [], roles: [] };

	const create = new RecordCreateState<Created, AssignmentDraft, CreateContext>({
		context: async () => {
			const [pool, codes, roles] = await Promise.all([api.schedule.pool(), api.schedule.codes(), api.roles.list()]);
			context = { pool, codes, roles };
			return context;
		},
		create: async (draft) => {
			const person = context.pool.find((item) => item.id === draft.userId);
			const user = person?.name || person?.username || '';
			if (context.codes.find((code) => code.id === draft.codeId)?.is_day_off) {
				// Work and a day off cannot share a day, so the person's work that day is released first.
				const work = await api.schedule.assignments.list({ start: draft.date, end: draft.date, user_id: draft.userId });
				for (const item of work) await api.schedule.assignments.remove(item.id);
				await api.schedule.daysOff.create({ date: draft.date, user_id: draft.userId, shift_code_id: draft.codeId });
				return { assignment: null, user };
			}
			if (!person?.outlet_id) throw new Error(format(scheduleText.notPlacedInBranch, { name: user || termText.employee }));
			const assignment = await api.schedule.assignments.create(person.outlet_id, { date: draft.date, user_id: draft.userId, shift_code_id: draft.codeId, role_id: draft.roleId });
			return { assignment, user };
		},
		name: (created) => created.user,
		message: (created) => (created.assignment ? format(scheduleText.scheduled, { name: created.user }) : format(scheduleText.markedDayOff, { name: created.user })),
		after: (created) => (created.assignment ? assignmentPath(created.assignment.id) : PAGES.schedule.path),
		text: createText('jadwal')
	});
</script>

<RecordCreateView {create} back={PAGES.schedule}>
	{#snippet form(props)}
		<AssignmentForm
			assignment={null}
			pool={props.context?.pool ?? []}
			codes={props.context?.codes ?? []}
			roles={props.context?.roles ?? []}
			{startDate}
			{startUser}
			busy={props.busy}
			error={props.error}
			fieldErrors={props.fieldErrors}
			onsave={(value) => props.onsave(value as AssignmentDraft)}
			onclose={props.onclose}
		/>
	{/snippet}
</RecordCreateView>
