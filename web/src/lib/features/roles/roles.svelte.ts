import { api } from '$lib/api';
import type { Permission, Role, RoleStation, RoleUpdate } from '$lib/api/types';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { ManageState } from '../manage/manage.svelte';
import { roleColumns } from './columns';

export type PermissionSection = { name: string; items: Permission[] };
export type PermissionGroup = { name: string; sections: PermissionSection[] };

/** The catalogue of permissions as the form shows it: groups, and sections inside each. */
export function groupPermissions(permissions: Permission[]): PermissionGroup[] {
	const groups = new Map<string, Map<string, Permission[]>>();
	for (const permission of permissions) {
		const sections = groups.get(permission.group_name) ?? new Map<string, Permission[]>();
		sections.set(permission.section, [...(sections.get(permission.section) ?? []), permission]);
		groups.set(permission.group_name, sections);
	}
	return [...groups].map(([name, sections]) => ({ name, sections: [...sections].map(([section, items]) => ({ name: section, items })) }));
}

export type RoleEntry = { name: string; description?: string; copy_from?: string };

export class RolesState extends ManageState<Role> {
	override readonly tables = ['roles', 'stations'];
	readonly sort = new ListSort('peran', sortKeys(roleColumns(this)), () => void this.queryChanged());

	permissions = $state<Permission[]>([]);
	stations = $state<RoleStation[]>([]);

	changeOpen = $state(false);
	bulkRemoveOpen = $state(false);

	readonly groups = $derived(groupPermissions(this.permissions));

	get canMarkProtected(): boolean {
		return this.items.some((role) => role.is_protected && role.held_by_viewer);
	}

	protected async fetch(): Promise<void> {
		const [roles, permissions, stations] = await Promise.all([api.roles.list(this.sort.param), api.roles.permissions(), api.roles.stations()]);
		this.items = roles;
		this.permissions = permissions;
		this.stations = stations;
	}

	protected label(role: Role): string {
		return role.name;
	}

	closeDialogs(): void {
		this.changeOpen = false;
		this.bulkRemoveOpen = false;
		this.actionError = '';
	}

	async changeSelected(changes: Record<string, string | number | boolean>): Promise<void> {
		await this.bulk('diubah', (ids) => api.roles.bulk.update(ids, changes as RoleUpdate), () => (this.changeOpen = false));
	}

	async removeSelected(): Promise<void> {
		await this.bulk('dihapus', (ids) => api.roles.bulk.remove(ids), () => (this.bulkRemoveOpen = false));
	}
}
