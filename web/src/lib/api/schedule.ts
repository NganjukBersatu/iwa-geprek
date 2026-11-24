import { bulkApi } from './bulk';
import { del, inBranch, patch, post, request, toQuery, type SortParam } from './http';
import type { Assignment, AssignmentCreate, AssignmentUpdate, DayOff, DayOffCreate, PoolUser, ShiftCode } from './types';

const ASSIGNMENTS = '/web/management/schedule/assignments';
const DAYS_OFF = '/web/management/schedule/days-off';

export type RangeParams = { start?: string; end?: string; user_id?: string; outlet_id?: string };

export const scheduleApi = {
	assignments: {
		list: (params: RangeParams & SortParam): Promise<Assignment[]> => request(`${ASSIGNMENTS}?${toQuery(params)}`),
		get: (id: string): Promise<Assignment> => request(`${ASSIGNMENTS}/${id}`),
		create: (outletId: string, body: AssignmentCreate): Promise<Assignment> => post(inBranch(ASSIGNMENTS, outletId), body),
		update: (id: string, body: AssignmentUpdate): Promise<Assignment> => patch(`${ASSIGNMENTS}/${id}`, body),
		remove: (id: string): Promise<void> => del(`${ASSIGNMENTS}/${id}`),
		swap: (firstId: string, secondId: string): Promise<{ first: Assignment; second: Assignment }> => post(`${ASSIGNMENTS}/swap`, { first_id: firstId, second_id: secondId }),
		bulk: bulkApi<AssignmentCreate, AssignmentUpdate>(ASSIGNMENTS)
	},
	daysOff: {
		list: (params: RangeParams): Promise<DayOff[]> => request(`${DAYS_OFF}?${toQuery(params)}`),
		create: (body: DayOffCreate): Promise<DayOff> => post(DAYS_OFF, body),
		remove: (id: string): Promise<void> => del(`${DAYS_OFF}/${id}`)
	},
	pool: (params: Pick<RangeParams, 'outlet_id'> = {}): Promise<PoolUser[]> => request(`/web/management/schedule/users?${toQuery(params)}`),
	codes: (): Promise<ShiftCode[]> => request('/web/management/shift-codes')
};
