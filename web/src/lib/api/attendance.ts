import { del, patch, post, request, toQuery, type SortParam } from './http';
import type { AttendanceEdit, AttendanceMark, AttendancePage, AttendanceRecord, AttendanceStatus } from './types';

const BASE = '/web/management/attendance';

export type AttendanceParams = SortParam & {
	start?: string;
	end?: string;
	user_id?: string;
	status?: AttendanceStatus;
	has_photo?: boolean;
	outside_schedule?: boolean;
	search?: string;
	outlet_id?: string;
	page?: number;
	size?: number;
};

export const attendanceApi = {
	list: (params: AttendanceParams): Promise<AttendancePage> => request(`${BASE}?${toQuery(params)}`),
	detail: (id: string): Promise<AttendanceRecord> => request(`${BASE}/${id}`),
	range: (params: Pick<AttendanceParams, 'start' | 'end' | 'user_id'>): Promise<AttendanceRecord[]> => request(`${BASE}/range?${toQuery(params)}`),
	mark: (body: AttendanceMark): Promise<AttendanceRecord> => post(`${BASE}/mark`, body),
	edit: (id: string, body: AttendanceEdit): Promise<AttendanceRecord> => patch(`${BASE}/${id}`, body),
	remove: (id: string): Promise<void> => del(`${BASE}/${id}`)
};
