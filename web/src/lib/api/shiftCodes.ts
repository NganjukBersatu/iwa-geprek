import { bulkApi } from './bulk';
import { del, patch, post, request, toQuery } from './http';
import type { CodeGroup, CodeGroupCreate, CodeGroupUpdate, ShiftCategory, ShiftCategoryUpdate } from './types';

const BASE = '/web/management/shift-code-groups';
const CATEGORY_BASE = '/web/management/shift-categories';

export const shiftCodesApi = {
	list: (sort?: string): Promise<CodeGroup[]> => request(`${BASE}?${toQuery({ sort })}`),
	categories: (): Promise<string[]> => request(`${BASE}/categories`),
	categorySettings: (): Promise<ShiftCategory[]> => request(CATEGORY_BASE),
	updateCategory: (id: string, body: ShiftCategoryUpdate): Promise<ShiftCategory> => patch(`${CATEGORY_BASE}/${id}`, body),
	removeCategory: (id: string): Promise<void> => del(`${CATEGORY_BASE}/${id}`),
	detail: (id: string): Promise<CodeGroup> => request(`${BASE}/${id}`),
	create: (body: CodeGroupCreate): Promise<CodeGroup> => post(BASE, body),
	update: (id: string, body: CodeGroupUpdate): Promise<CodeGroup> => patch(`${BASE}/${id}`, body),
	remove: (id: string): Promise<void> => del(`${BASE}/${id}`),
	bulk: bulkApi<CodeGroupCreate, CodeGroupUpdate>(BASE)
};
