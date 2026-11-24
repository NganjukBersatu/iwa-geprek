import { inBranch, post, request, toQuery } from './http';
import type { IngredientCountRequest, IngredientCountRequestPage } from './types';

const BASE = '/web/management/ingredient-count-requests';

export type IngredientCountRequestParams = { page?: number; size?: number };

export const ingredientCountRequestsApi = {
	list: (params: IngredientCountRequestParams): Promise<IngredientCountRequestPage> => request(`${BASE}?${toQuery(params)}`),
	get: (id: string): Promise<IngredientCountRequest> => request(`${BASE}/${id}`),
	/** Pengajuan terakhir periode berjalan cabang ini; kosong bila belum pernah diajukan. */
	current: (outletId: string): Promise<IngredientCountRequest | null> => request(inBranch(`${BASE}/current`, outletId)),
	submit: (outletId: string, note: string | null): Promise<IngredientCountRequest> => post(inBranch(BASE, outletId), { note }),
	markSeen: (id: string): Promise<void> => post(`${BASE}/${id}/seen`, {}),
	reject: (id: string): Promise<void> => post(`${BASE}/${id}/reject`, {})
};
