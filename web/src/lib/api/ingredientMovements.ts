import { bulkApi } from './bulk';
import { del, inBranch, patch, post, request, toQuery, upload, type SortParam } from './http';
import type { IngredientMovement, IngredientMovementPage, IngredientMovementUpdate, IngredientReceipt, IngredientTrial, IngredientWaste, WasteCause } from './types';

const BASE = '/web/management/ingredient-movements';

export type IngredientMovementParams = SortParam & { kind?: string; start?: string; end?: string; search?: string; page?: number; size?: number };

export const ingredientMovementsApi = {
	list: (params: IngredientMovementParams): Promise<IngredientMovementPage> => request(`${BASE}?${toQuery(params)}`),
	detail: (id: string): Promise<IngredientMovement> => request(`${BASE}/${id}`),
	causes: (): Promise<WasteCause[]> => request(`${BASE}/causes`),
	recordWaste: (outletId: string, body: IngredientWaste): Promise<IngredientMovement> => post(inBranch(`${BASE}/waste`, outletId), body),
	recordTrial: (outletId: string, body: IngredientTrial): Promise<IngredientMovement> => post(inBranch(`${BASE}/trials`, outletId), body),
	receive: (outletId: string, body: IngredientReceipt): Promise<IngredientMovement> => post(inBranch(`${BASE}/receipts`, outletId), body),
	update: (id: string, body: IngredientMovementUpdate): Promise<IngredientMovement> => patch(`${BASE}/${id}`, body),
	remove: (id: string): Promise<void> => del(`${BASE}/${id}`),
	uploadProof: (id: string, file: Blob): Promise<IngredientMovement> => upload(`${BASE}/${id}/proof`, 'file', file),
	bulk: bulkApi<IngredientReceipt, never>(BASE),
	wasteBulk: bulkApi<IngredientWaste, never>(`${BASE}/waste`),
	trialBulk: bulkApi<IngredientTrial, never>(`${BASE}/trials`)
};
