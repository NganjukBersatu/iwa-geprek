import { del, inBranch, patch, post, request, toQuery, upload, type SortParam } from './http';
import type { DayState, DayStatesAsk, Deposit, DepositCreate, DepositDays } from './types';

const BASE = '/web/management/deposits';

export type DepositRange = { start?: string; end?: string };

export const depositsApi = {
	days: (params: DepositRange & SortParam): Promise<DepositDays> => request(`${BASE}/days?${toQuery(params)}`),
	list: (params: DepositRange & { share_sort?: string }): Promise<Deposit[]> => request(`${BASE}?${toQuery(params)}`),
	/** One branch's days, which is what a deposit written for that branch is measured against. */
	daysOf: (outletId: string, range: DepositRange): Promise<DepositDays> => request(inBranch(`${BASE}/days?${toQuery(range)}`, outletId)),
	create: (outletId: string, body: DepositCreate): Promise<Deposit> => post(inBranch(BASE, outletId), body),
	setNote: (deposit: Deposit, note: string | null): Promise<Deposit> => patch(inBranch(`${BASE}/${deposit.id}`, deposit.outlet_id), { note }),
	uploadPhoto: (deposit: Deposit, file: Blob): Promise<Deposit> => upload(inBranch(`${BASE}/${deposit.id}/photo`, deposit.outlet_id), 'file', file),
	cancel: (deposit: Deposit): Promise<void> => del(inBranch(`${BASE}/${deposit.id}`, deposit.outlet_id)),
	/** Read right before money of these days changes, so a warning can name what was handed over. */
	dayStates: (asked: DayStatesAsk): Promise<DayState[]> => post(`${BASE}/day-states`, asked)
};
