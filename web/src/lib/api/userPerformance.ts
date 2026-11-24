import { request, toQuery } from './http';
import type { UserPerformance, UserPerformancePage } from './types';

const BASE = '/web/management/user-performance';

/** Daftar hanya per siklus; seluruh riwayat (all) hanya untuk satu karyawan. */
export type PerformanceListRange = 'cycle' | 'previous';
export type PerformanceRange = PerformanceListRange | 'all';

export type UserPerformanceQuery = { range: PerformanceListRange; search?: string; outlet_id?: string; sort?: string; page: number; size: number };

export const userPerformanceApi = {
	list: (query: UserPerformanceQuery): Promise<UserPerformancePage> => request(`${BASE}?${toQuery(query)}`),
	get: (userId: string, range: PerformanceRange): Promise<UserPerformance> => request(`${BASE}/${userId}?${toQuery({ range })}`)
};
