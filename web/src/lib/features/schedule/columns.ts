import type { Assignment, ShiftCode } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { dayLabel, formatDayMonth } from '$lib/date/range';
import { EMPTY_VALUE } from '$lib/format/currency';
import { termText } from '$lib/text/terms';
import { scheduleText } from '$lib/text/schedule';

/** Attendance is matched on screen from another list, so it is not sorted. */
export function assignmentColumns(codeOf: (id: string | null | undefined) => ShiftCode | undefined): Column<Assignment>[] {
	return [
		{ key: 'karyawan', label: termText.employee, align: 'left', value: (row) => row.user_username, sort: 'user' },
		{ key: 'tanggal', label: termText.date, align: 'left', value: (row) => `${dayLabel(row.date).weekday} ${formatDayMonth(row.date)}`, sort: 'date' },
		{ key: 'kode', label: termText.code, align: 'left', value: (row) => codeOf(row.shift_code_id)?.code ?? EMPTY_VALUE, sort: 'code' },
		{ key: 'peran', label: scheduleText.dayRole, align: 'left', value: (row) => row.role_name ?? EMPTY_VALUE, sort: 'role' },
		{ key: 'catatan', label: termText.note, align: 'left', value: (row) => row.note ?? '', sort: 'note' },
		{ key: 'kehadiran', label: scheduleText.attendance, align: 'left', value: () => '' }
	];
}
