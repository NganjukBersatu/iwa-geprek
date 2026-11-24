import type { Task } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { EMPTY_VALUE } from '$lib/format/currency';
import { isLate, momentLabel, ownerLabel } from './display';
import { personName } from './tasks.svelte';
import { termText } from '$lib/text/terms';
import { taskText } from '$lib/text/tasks';

export const taskColumns = (done: boolean): Column<Task>[] => [
	{ key: 'tugas', label: taskText.task, align: 'left', value: (row) => row.title, sort: 'title' },
	{ key: 'cabang', label: termText.branch, align: 'left', value: (row) => row.outlet?.name ?? EMPTY_VALUE, sort: 'outlet' },
	{ key: 'untuk', label: taskText.assignedTo, align: 'left', value: ownerLabel },
	{ key: 'pemberi', label: taskText.createdBy, align: 'left', value: (row) => personName(row.creator) || EMPTY_VALUE, sort: 'creator' },
	{ key: 'waktu', label: done ? taskText.done : taskText.deadline, value: momentLabel, class: (row) => (isLate(row) ? 'font-semibold text-danger-700' : ''), sort: 'moment' }
];
