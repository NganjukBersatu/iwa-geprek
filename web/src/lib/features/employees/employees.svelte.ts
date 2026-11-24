import { toast } from '$lib/components/feedback/toast.svelte';
import { api } from '$lib/api';
import type { Employee, EmployeeUpdate, Role } from '$lib/api/types';
import { Filters } from '$lib/components/filter/filters.svelte';
import { pageSize } from '$lib/components/pager/size.svelte';
import { collectPages } from '../manage/collect';
import { ManageState } from '../manage/manage.svelte';
import { branchList } from '$lib/stores/branch';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { employeeColumns } from './columns';
import { termText } from '$lib/text/terms';

export type EmployeeQuery = { search: string | null; role: string | null; branch: string | null; status: string | null };

const STATUS_ACTIVE = 'active';
const STATUS_INACTIVE = 'inactive';

export class EmployeesState extends ManageState<Employee> {
	override readonly tables = ['users', 'roles'];
	readonly sort = new ListSort('karyawan', sortKeys(employeeColumns(() => '')), () => void this.queryChanged());

	readonly filters = new Filters([
		{ kind: 'select', key: 'peran', label: termText.role, options: [] },
		{ kind: 'select', key: 'cabang', label: termText.branch, options: [] },
		{
			kind: 'select',
			key: 'status_karyawan',
			label: termText.status,
			options: [
				{ value: STATUS_ACTIVE, label: termText.active },
				{ value: STATUS_INACTIVE, label: termText.inactive }
			]
		}
	]);

	roles = $state<Role[]>([]);
	outlets = $state<{ id: string; name: string }[]>([]);

	changeOpen = $state(false);
	bulkRemoveOpen = $state(false);

	get query(): EmployeeQuery {
		return {
			search: this.search || null,
			role: this.filters.get('peran'),
			branch: this.filters.get('cabang'),
			status: this.filters.get('status_karyawan')
		};
	}

	roleOf = (id: string) => this.roles.find((role) => role.id === id);
	branchName = (id: string | null) => (id ? (this.outlets.find((outlet) => outlet.id === id)?.name ?? '—') : termText.allBranches);

	private params(page: number, size: number) {
		const query = this.query;
		return {
			search: query.search ?? undefined,
			role_id: query.role ?? undefined,
			outlet_id: query.branch ?? undefined,
			active: query.status === null ? undefined : query.status === STATUS_ACTIVE,
			sort: this.sort.param,
			page,
			size
		};
	}

	protected override allRows(): Promise<Employee[]> {
		return collectPages((page, size) => api.employees.list(this.params(page, size)));
	}

	protected async fetch(): Promise<void> {
		const query = this.query;
		const [page, roles, outlets] = await Promise.all([
			api.employees.list(this.params(this.page, pageSize.value)),
			api.roles.list(),
			branchList()
		]);
		this.items = page.items;
		this.total = page.total;
		this.roles = roles;
		this.outlets = outlets;
		this.filters.setOptions('peran', roles.map((role) => ({ value: role.id, label: role.name })));
		this.filters.setOptions('cabang', outlets.map((outlet) => ({ value: outlet.id, label: outlet.name })));
	}

	protected label(employee: Employee): string {
		return employee.name || employee.username;
	}

	private announce(text: string): void {
		toast.show(text);
	}

	closeDialogs(): void {
		this.changeOpen = false;
		this.bulkRemoveOpen = false;
		this.actionError = '';
	}

	async changeSelected(changes: Record<string, string | number | boolean>): Promise<void> {
		await this.bulk('diubah', (ids) => api.employees.bulk.update(ids, changes as EmployeeUpdate), () => (this.changeOpen = false));
	}

	async removeSelected(): Promise<void> {
		await this.bulk('dihapus', (ids) => api.employees.bulk.remove(ids), () => (this.bulkRemoveOpen = false));
	}
}
