import { del, patch, request, toQuery, type SortParam } from './http';
import type { Task, TaskInput, TaskOptions, TaskPage, TaskUpdate } from './types';

const BASE = '/v2/tasks';

export type TaskListParams = SortParam & {
	status: string;
	date_from?: string;
	date_to?: string;
	q?: string;
	assignee_id?: string;
	outlet_id?: string;
	page?: number;
	size?: number;
};

function formOf(fields: Record<string, string | null | undefined>, files: File[]): FormData {
	const form = new FormData();
	for (const [key, value] of Object.entries(fields)) if (value !== null && value !== undefined) form.append(key, value);
	for (const file of files) form.append('files', file);
	return form;
}

/** Tasks given to a person; the server tells what the signed-in person may do with each. */
export const tasksApi = {
	list: (params: TaskListParams): Promise<TaskPage> => request(`${BASE}?${toQuery(params)}`),
	get: (id: string): Promise<Task> => request(`${BASE}/${id}`),
	options: (params: { outlet_id?: string } = {}): Promise<TaskOptions> => request(`${BASE}/options?${toQuery(params)}`),
	create: (input: TaskInput, files: File[]): Promise<Task> =>
		request(BASE, {
			method: 'POST',
			body: formOf(
				{
					title: input.title,
					description: input.description || null,
					assignee_id: input.assignee_id,
					due_at: input.due_at,
					complete: String(input.complete),
					source_run_id: input.source_run_id
				},
				files
			)
		}),
	update: (id: string, body: TaskUpdate): Promise<Task> => patch(`${BASE}/${id}`, body),
	complete: (id: string, note: string, files: File[]): Promise<Task> =>
		request(`${BASE}/${id}/complete`, { method: 'POST', body: formOf({ note: note || null }, files) }),
	addAttachments: (id: string, files: File[]): Promise<Task> => request(`${BASE}/${id}/attachments`, { method: 'POST', body: formOf({}, files) }),
	/** Replaces the completion note of a task already sent; the proof is changed through the attachment routes. */
	fixCompletion: (id: string, note: string): Promise<Task> => patch(`${BASE}/${id}/completion`, { note }),
	removeAttachment: (id: string, attachmentId: string): Promise<Task> => request(`${BASE}/${id}/attachments/${attachmentId}`, { method: 'DELETE' }),
	remove: (id: string): Promise<void> => del(`${BASE}/${id}`)
};
