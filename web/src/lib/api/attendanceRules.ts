import { put, request } from './http';
import type { AttendanceRules, AttendanceRulesInput } from './types';

const BASE = '/web/management/attendance-rules';

export const attendanceRulesApi = {
	read: (): Promise<AttendanceRules> => request(BASE),
	update: (body: AttendanceRulesInput): Promise<AttendanceRules> => put(BASE, body)
};
