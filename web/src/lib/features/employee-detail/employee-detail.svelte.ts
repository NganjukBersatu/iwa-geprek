import { api } from '$lib/api';
import { ApiError } from '$lib/api/http';
import { userMessage } from '$lib/api/user-message';
import type { Employee, EmployeeUpdate, Role } from '$lib/api/types';
import { toast } from '$lib/components/feedback/toast.svelte';
import { branchList } from '$lib/stores/branch';
import { employeeDetailText } from '$lib/text/employee-detail';
import { format } from '$lib/text/format';

/** One employee: the account, the roles and branches the form offers, and the edit and delete actions. */
export class EmployeeDetailState {
	employee = $state<Employee | null>(null);
	roles = $state<Role[]>([]);
	outlets = $state<{ id: string; name: string }[]>([]);
	loading = $state(true);
	error = $state('');
	busy = $state(false);
	actionError = $state('');
	fieldErrors = $state<Record<string, string>>({});
	removing = $state(false);
	private token = 0;

	constructor(readonly id: string) {}

	branchName = (id: string | null): string => (id ? (this.outlets.find((outlet) => outlet.id === id)?.name ?? '—') : employeeDetailText.allBranches);

	/** Reloads without dimming the screen: what is shown stays until the fresh data arrives. */
	refresh(): Promise<void> {
		return this.load(true);
	}

	async load(quiet = false): Promise<void> {
		const token = ++this.token;
		if (!quiet) this.loading = true;
		try {
			const [employee, roles, outlets] = await Promise.all([api.employees.detail(this.id), api.roles.list(), branchList()]);
			if (token !== this.token) return;
			this.employee = employee;
			this.roles = roles;
			this.outlets = outlets.map((outlet) => ({ id: outlet.id, name: outlet.name }));
			this.error = '';
		} catch (error) {
			if (token !== this.token) return;
			if (!quiet) {
				this.employee = null;
				this.error = userMessage(error, employeeDetailText.loadFailed);
			}
		} finally {
			if (token === this.token) this.loading = false;
		}
	}

	askRemove(): void {
		this.actionError = '';
		this.removing = true;
	}

	closeDialogs(): void {
		this.removing = false;
		this.actionError = '';
		this.fieldErrors = {};
	}

	/** True when the account was saved, so the edit page returns to it. */
	async save(body: EmployeeUpdate): Promise<boolean> {
		const current = this.employee;
		if (!current) return false;
		if (!(await this.attempt(async () => (this.employee = await api.employees.update(current.id, body)), employeeDetailText.saveFailed))) return false;
		toast.show(format(employeeDetailText.saved, { name: this.employee?.name || this.employee?.username || '' }));
		return true;
	}

	/** True when the account was deleted, so the page returns to the list. */
	async remove(): Promise<boolean> {
		const current = this.employee;
		if (!current) return false;
		return this.attempt(() => api.employees.remove(current.id), employeeDetailText.removeFailed);
	}

	private async attempt(work: () => Promise<unknown>, fallback: string): Promise<boolean> {
		this.busy = true;
		this.actionError = '';
		this.fieldErrors = {};
		try {
			await work();
			return true;
		} catch (error) {
			this.fieldErrors = error instanceof ApiError ? error.fieldErrors : {};
			this.actionError = userMessage(error, fallback);
			return false;
		} finally {
			this.busy = false;
		}
	}
}
