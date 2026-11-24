import { api } from '$lib/api';
import type { Task, TaskOptions, TaskPerson } from '$lib/api/types';
import { Filters } from '$lib/components/filter/filters.svelte';
import { pageSize } from '$lib/components/pager/size.svelte';
import type { DateRange } from '$lib/date/range';
import { TASK_TABLES } from '$lib/live/tables';
import { ManageState } from '../manage/manage.svelte';
import { reportPresets } from '../report/filters';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { taskColumns } from './columns';
import { termText } from '$lib/text/terms';

export const STATUS_OPEN = 'belum';
export const STATUS_DONE = 'selesai';

export type TaskQuery = { status: string; search: string | null; branch: string | null; assignee: string | null; range: DateRange | null };

export const personName = (person: TaskPerson | null): string => (person ? person.name || person.username : '');

export class TasksState extends ManageState<Task> {
	readonly sort = new ListSort('tugas', sortKeys(taskColumns(false)), () => void this.queryChanged());
	override readonly tables = TASK_TABLES;

	readonly filters = new Filters([
		{ kind: 'select', key: 'cabang', label: termText.branch, options: [] },
		{ kind: 'select', key: 'karyawan', label: termText.employee, options: [] },
		{ kind: 'date', key: 'rentang', label: termText.range, presets: reportPresets, reach: 'future' }
	]);

	status = $state<string>(STATUS_OPEN);
	options = $state<TaskOptions | null>(null);

	get query(): TaskQuery {
		return {
			status: this.status,
			search: this.search || null,
			branch: this.filters.get('cabang'),
			assignee: this.filters.get('karyawan'),
			range: this.filters.range('rentang')
		};
	}

	protected async fetch(): Promise<void> {
		const query = this.query;
		const [page, options] = await Promise.all([
			api.tasks.list({
				status: query.status,
				date_from: query.range?.from,
				date_to: query.range?.to,
				q: query.search ?? undefined,
				assignee_id: query.assignee ?? undefined,
				outlet_id: query.branch ?? undefined,
				sort: this.sort.param,
				page: this.page,
				size: pageSize.value
			}),
			api.tasks.options()
		]);
		this.options = options;
		this.filters.setOptions('cabang', options.outlets.map((outlet) => ({ value: outlet.id, label: outlet.name })));
		this.filters.setOptions('karyawan', options.assignees.map((person) => ({ value: person.id, label: personName(person) })));
		this.items = page.items;
		this.total = page.total;
	}

	protected label(task: Task): string {
		return task.title;
	}
}
