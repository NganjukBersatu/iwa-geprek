import { request, toQuery, type SortParam } from './http';
import type { MoneyChangePage, MoneyChangeReport, MoneySubject } from './types';

const BASE = '/web/management/money-changes';

export type MoneyChangeParams = SortParam & { start?: string; end?: string; subject?: MoneySubject; page: number; size: number };

export const moneyChangesApi = {
	list: (params: MoneyChangeParams): Promise<MoneyChangeReport> => request(`${BASE}?${toQuery(params)}`),
	ofSession: (sessionId: string, page: number, size: number, sort?: string): Promise<MoneyChangePage> => request(`${BASE}/sessions/${sessionId}?${toQuery({ page, size, sort })}`)
};
