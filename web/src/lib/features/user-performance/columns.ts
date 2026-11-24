import type { UserPerformanceRow } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { EMPTY_VALUE, formatNumber } from '$lib/format/currency';
import { formatDuration } from '$lib/format/datetime';
import { format } from '$lib/text/format';
import { userPerformanceText as t } from '$lib/text/user-performance';
import { percentText, periodText, starsText } from './labels';

export type PerformanceRow = UserPerformanceRow & { id: string };

export const performanceColumns: Column<PerformanceRow>[] = [
	{ key: 'karyawan', label: t.columns.employee, align: 'left', value: (row) => row.name, sort: 'name' },
	{ key: 'cabang', label: t.columns.branch, align: 'left', value: (row) => row.outlet_name ?? t.allBranches, sort: 'outlet' },
	{ key: 'periode', label: t.columns.period, align: 'left', value: (row) => periodText(row.start, row.end) },
	{ key: 'penilaian', label: t.columns.rating, align: 'left', value: (row) => starsText(row.stars), sort: 'stars' },
	{ key: 'tepat', label: t.columns.onTime, value: (row) => percentText(row.on_time_percent), sort: 'on_time' },
	{ key: 'telat', label: t.columns.late, value: (row) => formatNumber(row.late, 0), sort: 'late' },
	{ key: 'absen', label: t.columns.absent, value: (row) => formatNumber(row.absent, 0), sort: 'absent' },
	{ key: 'kerja', label: t.columns.work, value: (row) => formatDuration(row.work_minutes), sort: 'work' },
	{ key: 'lembur', label: t.columns.overtime, value: (row) => (row.overtime_minutes > 0 ? formatDuration(row.overtime_minutes) : EMPTY_VALUE), sort: 'overtime' },
	{ key: 'tugas', label: t.columns.tasks, value: (row) => format(t.tasksOf, { done: formatNumber(row.tasks_done, 0), assigned: formatNumber(row.tasks_assigned, 0) }), sort: 'tasks' }
];

/** The download also carries the details that do not fit the table. */
export const performanceExportColumns: Column<PerformanceRow>[] = [
	...performanceColumns,
	{ key: 'peran', label: t.columns.role, align: 'left', value: (row) => row.role_name ?? EMPTY_VALUE },
	{ key: 'izin', label: t.columns.leave, value: (row) => formatNumber(row.leave, 0) },
	{ key: 'hari', label: t.columns.countedDays, value: (row) => formatNumber(row.counted_days, 0) }
];
