import { EMPTY_VALUE, formatNumberOrDash } from '$lib/format/currency';
import { batchText } from '$lib/text/batches';
import { batchRunText } from '$lib/text/batch-runs';
import { format } from '$lib/text/format';

export type BatchKind = 'outlet' | 'routine';

export const FILL_ONE = 'one';
export const FILL_EACH = 'each';

export const TARGET_SHIFT = 'shift';
export const TARGET_USER = 'users';

export const TARGETS = [
	{ value: TARGET_SHIFT, label: batchText.targetShift },
	{ value: TARGET_USER, label: batchText.targetUser }
];

export const FILL_MODES = [
	{ value: FILL_ONE, label: batchText.fillOne },
	{ value: FILL_EACH, label: batchText.fillEach }
];

/** The recipients of one routine task as text: its shift codes, or the names of the people picked. */
export function recipientLabel(batch: { target: string; shift_codes: { code: string }[]; user: { name: string }[] }): string {
	if (batch.target !== TARGET_USER) return batch.shift_codes.map((code) => code.code).join(', ');
	return batch.user.length === 0 ? batchText.noRecipient : batch.user.map((person) => person.name).join(', ');
}

export const STATUS_FILTER = [
	{ value: 'true', label: batchText.statusActive },
	{ value: 'false', label: batchText.statusInactive }
];

export const REPEAT_FILTER = [
	{ value: 'day', label: batchText.repeatDay },
	{ value: 'week', label: batchText.repeatWeek },
	{ value: 'month', label: batchText.repeatMonth }
];

export const PROBLEM_FILTER = [
	{ value: 'true', label: batchRunText.problemYes },
	{ value: 'false', label: batchRunText.problemNo }
];

export const FOLLOW_UP_FILTER = [
	{ value: 'none', label: batchRunText.followNone },
	{ value: 'open', label: batchRunText.followOpen },
	{ value: 'done', label: batchRunText.followDone }
];

/** The follow-up of one filling in a line for the history list. */
export function followUpLabel(run: { follow_up_total: number; follow_up_open: number }): string {
	if (run.follow_up_total === 0) return EMPTY_VALUE;
	return run.follow_up_open === 0 ? format(batchRunText.followDoneCount, { count: run.follow_up_total }) : format(batchRunText.followOpenCount, { open: run.follow_up_open, total: run.follow_up_total });
}

const CHANGE_WORDS: Record<string, string> = { fix: batchRunText.wordFix, cancel: batchRunText.wordCancel, delete: batchRunText.wordDelete };

/** The word for one kind of change to a filling; empty when it was never changed. */
export const changeWord = (action: string | null): string => (action ? (CHANGE_WORDS[action] ?? action) : '');

/** The change to a filling and who made it, as one phrase. */
export const changeLabel = (action: string | null, by: string | null): string => (action ? format(batchRunText.changedBy, { word: changeWord(action), name: by ?? EMPTY_VALUE }) : '');

export const kindShort = (kind: string): string => (kind === 'routine' ? batchText.kinds.routine.short : batchText.kinds.outlet.short);
export const fillLabel = (mode: string): string => FILL_MODES.find((item) => item.value === mode)?.label ?? mode;

export const WEEKDAYS = [batchText.mondayShort, batchText.tuesdayShort, batchText.wednesdayShort, batchText.thursdayShort, batchText.fridayShort, batchText.saturdayShort, batchText.sundayShort];

export const PHOTO_KIND = 'photo';
export const TOGGLE_KIND = 'toggle';
export const NUMBER_KIND = 'number';

export const ITEM_KINDS = [
	{ value: TOGGLE_KIND, label: batchText.kindOkOrProblem },
	{ value: NUMBER_KIND, label: batchText.kindNumber },
	{ value: 'text', label: batchText.kindText },
	{ value: PHOTO_KIND, label: batchText.kindPhoto }
];

export const TOGGLE_OPTIONS = [
	{ value: 'ok', label: batchRunText.toggleOk },
	{ value: 'problem', label: batchRunText.toggleProblem }
];

export type RepeatUnit = 'day' | 'week' | 'month';

/** The units of repeating with the limit of the number, the same as the server's. */
export const REPEAT_UNITS: { value: RepeatUnit; label: string; max: number }[] = [
	{ value: 'day', label: batchText.unitDay, max: 365 },
	{ value: 'week', label: batchText.unitWeek, max: 52 },
	{ value: 'month', label: batchText.unitMonth, max: 12 }
];

export const daysLabel = (weekdays: number[]): string => (weekdays.length === 0 ? batchText.everyDay : weekdays.map((day) => WEEKDAYS[day]).join(', '));

const dayOfMonth = (iso: string): number => Number(iso.slice(8, 10));
/** Monday is 0, the order of WEEKDAYS; the date is read as a calendar date, not a point in time. */
const weekdayOf = (iso: string): number => (new Date(`${iso}T00:00:00Z`).getUTCDay() + 6) % 7;

type Repeating = { repeat_unit: string | null; repeat_every: number; starts_on: string | null; weekdays: number[] };

/** The repeat of one task as a short sentence; an old task without a unit still repeats by its days. */
export function repeatLabel(batch: Repeating): string {
	const { repeat_unit: unit, repeat_every: every, starts_on: start } = batch;
	if (!unit || !start) return daysLabel(batch.weekdays);
	if (unit === 'day') return every === 1 ? batchText.everyDay : format(batchText.repeatEveryDays, { every });
	const weekday = WEEKDAYS[weekdayOf(start)] ?? '';
	if (unit === 'week') return format(every === 1 ? batchText.repeatEveryWeek : batchText.repeatEveryWeeks, { every, weekday });
	return format(every === 1 ? batchText.repeatEveryMonth : batchText.repeatEveryMonths, { every, day: dayOfMonth(start) });
}

export type FollowUp = { outletId: string; sourceRunId: string; title: string; description: string };

/** The start of a follow-up task from one filling: where it came from, the answers that went wrong, and the notes the employee wrote. */
export function followUpOf(run: { id: string; batch_name: string; outlet_id: string; outlet_name: string; completed_by: string | null; answers: { label: string; kind: string; value: string | null }[] }, when: string): FollowUp {
	const problems = run.answers.filter((answer) => answer.kind === TOGGLE_KIND && answer.value === 'problem').map((answer) => answer.label);
	const notes = run.answers.filter((answer) => answer.kind === 'text' && answer.value).map((answer) => `${answer.label}: ${answer.value}`);
	const origin = format(batchRunText.followUpOrigin, { name: run.batch_name, when, by: run.completed_by ?? EMPTY_VALUE, outlet: run.outlet_name });
	const found = problems.length > 0 ? [format(batchRunText.followUpProblems, { labels: problems.join(', ') })] : [];
	return { outletId: run.outlet_id, sourceRunId: run.id, title: format(batchRunText.followUpTitle, { name: run.batch_name }), description: [origin, ...found, ...notes, '', batchRunText.followUpToDo].join('\n') };
}

/** One answer as the text the admin reads; an optional answer that was skipped shows as the empty mark. */
export function answerText(kind: string, value: string | null): string {
	if (value === null) return EMPTY_VALUE;
	if (kind === TOGGLE_KIND) return TOGGLE_OPTIONS.find((option) => option.value === value)?.label ?? value;
	if (kind === NUMBER_KIND) return formatNumberOrDash(value);
	return value;
}
