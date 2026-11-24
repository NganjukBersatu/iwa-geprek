import { del, patch, post, put, request, toQuery } from './http';
import type { Branch, BranchCreate, BranchPeriodChange, BranchReadiness, BranchRemoval, BranchUpdate } from './types';

const BASE = '/web/management/branches';

export const branchesApi = {
	list: (sort?: string): Promise<Branch[]> => request(`${BASE}?${toQuery({ sort })}`),
	detail: (id: string): Promise<Branch> => request(`${BASE}/${id}`),
	create: (body: BranchCreate): Promise<Branch> => post(BASE, body),
	readiness: (id: string): Promise<BranchReadiness> => request(`${BASE}/${id}/readiness`),
	update: (id: string, body: BranchUpdate): Promise<Branch> => patch(`${BASE}/${id}`, body),
	adjustPeriod: (id: string, originalStart: string, body: BranchPeriodChange): Promise<void> => put(`${BASE}/${id}/periods/${originalStart}`, body),
	resetPeriod: (id: string, start: string): Promise<void> => del(`${BASE}/${id}/periods/${start}`),
	/** Satu langkah hapus permanen; dipanggil lagi sampai selesai, dan panggilan ulang melanjutkan sisanya. */
	removeStep: (id: string, name: string): Promise<BranchRemoval> => post(`${BASE}/${id}/removal`, { name })
};
