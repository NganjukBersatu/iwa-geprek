import { ServerClock } from '$lib/time/server-clock';
import type { Task } from '$lib/api/types';
import { EMPTY_VALUE } from '$lib/format/currency';
import { formatDateTime } from '$lib/format/datetime';
import { personName } from './tasks.svelte';

/** An open task whose deadline has passed. */
export function isLate(task: Task): boolean {
	return task.status !== 'selesai' && task.due_at !== null && new Date(task.due_at).getTime() < ServerClock.nowMillis();
}

/** Who the task is given to. */
export function ownerLabel(task: Task): string {
	return personName(task.assignee) || EMPTY_VALUE;
}

/** The finish time of a done task, the deadline of an open one. */
export function momentLabel(task: Task): string {
	const at = task.status === 'selesai' ? task.completed_at : task.due_at;
	return at ? formatDateTime(at) : EMPTY_VALUE;
}
