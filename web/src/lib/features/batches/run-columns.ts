import type { BatchRun } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { formatDate } from '$lib/date/range';
import { EMPTY_VALUE } from '$lib/format/currency';
import { formatTime } from '$lib/format/datetime';
import { batchRunText } from '$lib/text/batch-runs';
import { format } from '$lib/text/format';
import { changeLabel, followUpLabel, kindShort } from './constants';

export const runColumns: Column<BatchRun>[] = [
	{ key: 'date', label: batchRunText.columnDate, align: 'left', value: (row) => formatDate(row.day), sort: 'day' },
	{ key: 'task', label: batchRunText.columnTask, align: 'left', value: (row) => row.batch_name, sort: 'name' },
	{ key: 'kind', label: batchRunText.columnKind, align: 'left', value: (row) => kindShort(row.kind) },
	{ key: 'filler', label: batchRunText.columnFilledBy, align: 'left', value: (row) => row.completed_by ?? EMPTY_VALUE },
	{ key: 'time', label: batchRunText.columnDoneAt, value: (row) => formatTime(row.completed_at), sort: 'completed' },
	{ key: 'change', label: batchRunText.columnChange, align: 'left', value: (row) => changeLabel(row.last_action, row.fixed_by) || EMPTY_VALUE },
	{ key: 'followUp', label: batchRunText.columnFollowUp, align: 'left', value: (row) => followUpLabel(row) },
	{ key: 'problems', label: batchRunText.columnProblems, value: (row) => (row.problems > 0 ? format(batchRunText.problemsCount, { count: row.problems }) : batchRunText.noProblems) }
];
