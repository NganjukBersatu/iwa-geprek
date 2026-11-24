import { api } from '$lib/api';
import type { AttendanceRecord, AttendanceStatus } from '$lib/api/types';
import { Filters } from '$lib/components/filter/filters.svelte';
import { pageSize } from '$lib/components/pager/size.svelte';
import { reportPresets } from '$lib/features/report/filters';
import { ManageState } from '../manage/manage.svelte';
import { branchList } from '$lib/stores/branch';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { attendanceColumns } from './columns';
import { STATUS_LABELS } from './labels';
import { termText } from '$lib/text/terms';
import { attendanceListText } from '$lib/text/attendance-list';

export type AttendanceQuery = {
	search: string | null;
	branch: string | null;
	status: string | null;
	range: { from: string; to: string } | null;
	photo: string | null;
	schedule: string | null;
};

export type MapView = { record: AttendanceRecord; side: 'in' | 'out' };

const YES = 'yes';

export class AttendanceListState extends ManageState<AttendanceRecord> {
	override readonly tables = ['attendance_records', 'schedules'];
	readonly sort = new ListSort('absensi', sortKeys(attendanceColumns), () => void this.queryChanged());

	readonly filters = new Filters([
		{ kind: 'select', key: 'cabang', label: termText.branch, options: [] },
		{ kind: 'date', key: 'rentang', label: termText.range, presets: reportPresets, reach: 'past' },
		{ kind: 'select', key: 'status_absen', label: termText.status, options: Object.entries(STATUS_LABELS).map(([value, label]) => ({ value, label })) },
		{ kind: 'select', key: 'foto', label: termText.photo, options: [{ value: YES, label: attendanceListText.hasPhoto }, { value: 'no', label: attendanceListText.noPhoto }] },
		{ kind: 'select', key: 'jadwal', label: termText.schedule, options: [{ value: YES, label: attendanceListText.offSchedule }, { value: 'no', label: attendanceListText.onSchedule }] }
	]);


	get query(): AttendanceQuery {
		return {
			search: this.search || null,
			branch: this.filters.get('cabang'),
			status: this.filters.get('status_absen'),
			range: this.filters.range('rentang'),
			photo: this.filters.get('foto'),
			schedule: this.filters.get('jadwal')
		};
	}

	protected async fetch(): Promise<void> {
		const query = this.query;
		const outlets = await branchList();
		this.filters.setOptions('cabang', outlets.map((outlet) => ({ value: outlet.id, label: outlet.name })));
		const page = await api.attendance.list({
			search: query.search ?? undefined,
			outlet_id: query.branch ?? undefined,
			status: (query.status as AttendanceStatus | null) ?? undefined,
			start: query.range?.from,
			end: query.range?.to,
			has_photo: query.photo === null ? undefined : query.photo === YES,
			outside_schedule: query.schedule === null ? undefined : query.schedule === YES,
			sort: this.sort.param,
			page: this.page,
			size: pageSize.value
		});
		this.items = page.items;
		this.total = page.total;
	}

	protected label(record: AttendanceRecord): string {
		return record.name || record.username;
	}

	closeDialogs(): void {
		this.actionError = '';
	}
}
