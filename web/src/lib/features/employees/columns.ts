import type { Employee } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { termText } from '$lib/text/terms';

export const employeeColumns = (branchName: (id: string | null) => string): Column<Employee>[] => [
	{ key: 'karyawan', label: termText.employee, align: 'left', value: (row) => row.name || row.username, sort: 'name' },
	{ key: 'peran', label: termText.role, align: 'left', value: (row) => row.role_name, sort: 'role' },
	{ key: 'cabang', label: termText.branch, align: 'left', value: (row) => branchName(row.outlet_id), sort: 'outlet' },
	{ key: 'status', label: termText.status, align: 'left', value: (row) => (row.is_active ? termText.active : termText.inactive), sort: 'active' }
];
