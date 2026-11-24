import type { Role } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { EMPTY_VALUE } from '$lib/format/currency';
import type { RolesState } from './roles.svelte';
import { roleText } from '$lib/text/roles';
import { format } from '$lib/text/format';

export const roleColumns = (roles: RolesState): Column<Role>[] => [
	{ key: 'peran', label: roleText.role, align: 'left', value: (row) => row.name, sort: 'name' },
	{ key: 'keterangan', label: roleText.description, align: 'left', value: (row) => row.description ?? EMPTY_VALUE, sort: 'description' },
	{ key: 'izin', label: roleText.permissions, value: (row) => (row.full_access ? roleText.allPermissions : format(roleText.paidOfDue, { paid: row.permissions.length, due: roles.permissions.length })), sort: 'permissions' }
];
