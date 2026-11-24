import { dropMissingBranch } from '$lib/stores/branch';
import { inBranch, request, toQuery } from './http';
import type { BranchPeriod, OutletOption, OutletPage } from './types';

const BASE = '/web/management/outlets';

export type OutletSearchParams = { search?: string; page?: number; size?: number };

export const outletsApi = {
	list: async (): Promise<OutletOption[]> => {
		const outlets = await request<OutletOption[]>(BASE, undefined, false);
		dropMissingBranch(outlets);
		return outlets;
	},
	search: (params: OutletSearchParams): Promise<OutletPage> => request(`${BASE}/search?${toQuery(params)}`),
	/** Periode yang sudah mulai, yang berjalan paling atas; tanpa cabang berarti semua cabang yang boleh dilihat. */
	periods: (outletId?: string): Promise<BranchPeriod[]> => request(outletId ? inBranch(`${BASE}/periods`, outletId) : `${BASE}/periods`)
};
