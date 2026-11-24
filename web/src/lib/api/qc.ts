import { inBranch, request, toQuery, type SortParam } from './http';
import type { CheckStatus, NonCashChecks } from './types';
import type { NonCashCheckRow } from './types';

const BASE = '/web/management/non-cash-checks';

export type CheckParams = SortParam & { start?: string; end?: string; status?: CheckStatus | 'all' };

export const qcApi = {
	list: (params: CheckParams): Promise<NonCashChecks> => request(`${BASE}?${toQuery(params)}`),
	save: (row: NonCashCheckRow, bankAmount: number): Promise<NonCashCheckRow> => request(inBranch(`${BASE}/${row.date}`, row.outlet_id), { method: 'PUT', body: JSON.stringify({ bank_amount: bankAmount }) }),
	remove: (row: NonCashCheckRow): Promise<void> => request(inBranch(`${BASE}/${row.date}`, row.outlet_id), { method: 'DELETE' })
};
