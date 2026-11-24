import { controlText } from '$lib/text/controls';
import { QUIET_VALUE } from '$lib/components/table/quiet-value';
import type { AttendanceRecord } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { dayLabel, formatDayMonth } from '$lib/date/range';
import { EMPTY_VALUE } from '$lib/format/currency';
import { formatTime } from '$lib/format/datetime';
import { STATUS_LABELS } from './labels';
import { termText } from '$lib/text/terms';
import { attendanceListText } from '$lib/text/attendance-list';
import { format } from '$lib/text/format';

const time = (iso: string | null) => (iso ? formatTime(iso) : EMPTY_VALUE);

/** Only the core columns always show; work hours, penalty, proof, and note are in the detail page that a row opens. */
export const attendanceColumns: Column<AttendanceRecord>[] = [
	{ key: 'karyawan', label: termText.employee, align: 'left', value: (row) => row.name || row.username, sort: 'name' },
	{ key: 'tanggal', label: termText.date, align: 'left', value: (row) => `${dayLabel(row.date).weekday} ${formatDayMonth(row.date)}`, sort: 'date' },
	{ key: 'kode', label: termText.code, align: 'left', value: (row) => row.shift_code ?? EMPTY_VALUE, sort: 'code' },
	{ key: 'masuk', label: attendanceListText.clockedIn, align: 'left', value: (row) => time(row.clock_in_at), sort: 'clock_in' },
	{ key: 'pulang', label: attendanceListText.clockedOut, align: 'left', value: (row) => time(row.clock_out_at), sort: 'clock_out' },
	{ key: 'telat', label: attendanceListText.late, value: (row) => (row.late_minutes > 0 ? format(controlText.minutesCount, { count: row.late_minutes }) : EMPTY_VALUE), class: (row) => (row.late_minutes > 0 ? 'text-warning-700' : QUIET_VALUE) },
	{ key: 'status', label: termText.status, align: 'left', value: (row) => STATUS_LABELS[row.status], sort: 'status' }
];
