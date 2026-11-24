import type { Branch } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { EMPTY_VALUE, formatRupiah } from '$lib/format/currency';
import { termText } from '$lib/text/terms';
import { actionText } from '$lib/text/actions';
import { branchText } from '$lib/text/branches';
import { format } from '$lib/text/format';

export const branchColumns: Column<Branch>[] = [
	{ key: 'cabang', label: termText.branch, align: 'left', value: (row) => row.name, sort: 'name' },
	{ key: 'titik', label: branchText.attendancePoint, align: 'left', value: (row) => (row.latitude !== null && row.longitude !== null ? `${row.latitude.toFixed(5)}, ${row.longitude.toFixed(5)}` : termText.notSet), sort: 'location' },
	{ key: 'radius', label: branchText.radius, value: (row) => format(branchText.metersCount, { count: row.attendance_radius_meters }), sort: 'radius' },
	{ key: 'laci', label: branchText.drawerFloat, value: (row) => (row.cash_float !== null ? formatRupiah(Number(row.cash_float)) : EMPTY_VALUE), sort: 'cash_float' },
	{ key: 'status', label: termText.status, align: 'left', value: (row) => (row.is_active ? termText.active : actionText.close), sort: 'status' }
];
