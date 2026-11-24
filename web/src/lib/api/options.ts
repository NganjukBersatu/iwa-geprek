import { bulkApi } from './bulk';
import { RECIPE_CHOICE_SIZE } from './recipes';
import { del, inBranch, patch, post, put, request, toQuery } from './http';
import type {
	Extra,
	ExtraCategory,
	ExtraCreate,
	ExtraUpdate,
	IngredientOption,
	OptionMenu,
	OptionRecipeResult,
	OptionRecipeSave,
	VariantGroup,
	VariantGroupCreate,
	VariantGroupUpdate
} from './types';

const BASE = '/web/management';

export const optionsApi = {
	groups: (sort?: string): Promise<VariantGroup[]> => request(`${BASE}/variant-groups?${toQuery({ sort })}`),
	group: (id: string): Promise<VariantGroup> => request(`${BASE}/variant-groups/${id}`),
	createGroup: (body: VariantGroupCreate): Promise<VariantGroup> => post(`${BASE}/variant-groups`, body),
	updateGroup: (id: string, body: VariantGroupUpdate): Promise<VariantGroup> => patch(`${BASE}/variant-groups/${id}`, body),
	removeGroup: (id: string): Promise<void> => del(`${BASE}/variant-groups/${id}`),
	groupsOf: (outletId: string): Promise<VariantGroup[]> => request(inBranch(`${BASE}/variant-groups`, outletId)),
	saveChoiceRecipe: (outletId: string, choiceId: string, body: OptionRecipeSave): Promise<OptionRecipeResult> => put(inBranch(`${BASE}/variant-groups/choices/${choiceId}/recipe`, outletId), body),
	groupsBulk: bulkApi<VariantGroupCreate, VariantGroupUpdate>(`${BASE}/variant-groups`),
	extras: (sort?: string): Promise<Extra[]> => request(`${BASE}/extras?${toQuery({ sort })}`),
	categories: (): Promise<ExtraCategory[]> => request(`${BASE}/extras/categories`),
	extra: (id: string): Promise<Extra> => request(`${BASE}/extras/${id}`),
	createExtra: (body: ExtraCreate): Promise<Extra> => post(`${BASE}/extras`, body),
	updateExtra: (id: string, body: ExtraUpdate): Promise<Extra> => patch(`${BASE}/extras/${id}`, body),
	removeExtra: (id: string): Promise<void> => del(`${BASE}/extras/${id}`),
	extrasOf: (outletId: string): Promise<Extra[]> => request(inBranch(`${BASE}/extras`, outletId)),
	saveExtraRecipe: (outletId: string, extraId: string, body: OptionRecipeSave): Promise<OptionRecipeResult> => put(inBranch(`${BASE}/extras/${extraId}/recipe`, outletId), body),
	extrasBulk: bulkApi<ExtraCreate, ExtraUpdate>(`${BASE}/extras`),
	menus: (): Promise<OptionMenu[]> => request(`${BASE}/option-menus`),
	ingredients: (outletId: string, search: string, page: number): Promise<IngredientOption[]> =>
		request(inBranch(`${BASE}/option-ingredients?${toQuery({ search, page, size: RECIPE_CHOICE_SIZE })}`, outletId))
};
