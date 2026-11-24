import { bulkApi } from './bulk';
import { del, inBranch, patch, post, put, request, toQuery, upload, type SortParam } from './http';
import type { CatalogEntry, CatalogLink, Ingredient, IngredientCreate, IngredientEverywhere, IngredientImpact, IngredientOptions, IngredientUpdate } from './types';

const BASE = '/web/management/ingredients';

/** indirect: true hanya bahan tidak langsung, false hanya yang dipotong resep, kosong keduanya. */
export type IngredientParams = SortParam & { search?: string; page?: number; size?: number; outlet_id?: string; indirect?: boolean };
export type IngredientPage = { items: Ingredient[]; total: number; page: number; size: number; unlinked: number };

export const ingredientsApi = {
	list: (params: IngredientParams): Promise<IngredientPage> => request(`${BASE}?${toQuery(params)}`),
	detail: (id: string): Promise<Ingredient> => request(`${BASE}/${id}`),
	options: (): Promise<IngredientOptions> => request(`${BASE}/options`),
	create: (outletId: string, body: IngredientCreate): Promise<Ingredient> => post(inBranch(BASE, outletId), body),
	update: (id: string, body: IngredientUpdate): Promise<Ingredient> => patch(`${BASE}/${id}`, body),
	impact: (id: string): Promise<IngredientImpact> => request(`${BASE}/${id}/impact`),
	remove: (id: string): Promise<void> => del(`${BASE}/${id}`),
	uploadPhoto: (id: string, file: Blob): Promise<Ingredient> => upload(`${BASE}/${id}/photo`, 'file', file),
	createEverywhere: (body: IngredientCreate): Promise<IngredientEverywhere> => post(`${BASE}/all-branches`, body),
	catalog: (): Promise<CatalogEntry[]> => request(`${BASE}/catalog`),
	removeCatalog: (id: string): Promise<void> => del(`${BASE}/catalog/${id}`),
	link: (id: string, body: CatalogLink): Promise<Ingredient> => put(`${BASE}/${id}/catalog`, body),
	bulk: bulkApi<IngredientCreate, IngredientUpdate>(BASE),
	removePhoto: (id: string): Promise<Ingredient> => request(`${BASE}/${id}/photo`, { method: 'DELETE' })
};
