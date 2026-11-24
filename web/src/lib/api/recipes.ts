import { inBranch, put, request, toQuery } from './http';
import type { IngredientOption, Recipe, RecipePage, RecipeSave, RecipeSaveResult } from './types';

const BASE = '/web/management/recipes';
// Satu halaman pilihan bahan resep; halaman berikutnya diminta saat daftar digulir.
export const RECIPE_CHOICE_SIZE = 50;

export type RecipeParams = { search?: string; recipe?: string; page?: number; size?: number };

export const recipesApi = {
	list: (params: RecipeParams): Promise<RecipePage> => request(`${BASE}?${toQuery(params)}`),
	of: (outletId: string, menuId: string): Promise<Recipe> => request(inBranch(`${BASE}/${menuId}`, outletId)),
	ingredients: (outletId: string, search: string, page: number): Promise<IngredientOption[]> =>
		request(inBranch(`${BASE}/ingredients?${toQuery({ search, page, size: RECIPE_CHOICE_SIZE })}`, outletId)),
	save: (outletId: string, menuId: string, body: RecipeSave): Promise<RecipeSaveResult> => put(inBranch(`${BASE}/${menuId}`, outletId), body)
};
