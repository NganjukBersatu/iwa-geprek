import { del, patch, post, request, toQuery } from './http';
import type { MenuCategoryCreate, MenuCategoryRecord, MenuCategoryUpdate } from './types';

const BASE = '/web/management/menu-categories';

export const menuCategoriesApi = {
	list: (sort?: string): Promise<MenuCategoryRecord[]> => request(`${BASE}?${toQuery({ sort })}`),
	create: (body: MenuCategoryCreate): Promise<MenuCategoryRecord> => post(BASE, body),
	update: (id: string, body: MenuCategoryUpdate): Promise<MenuCategoryRecord> => patch(`${BASE}/${id}`, body),
	remove: (id: string): Promise<void> => del(`${BASE}/${id}`)
};
