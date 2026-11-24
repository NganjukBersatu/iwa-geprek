import { bulkApi } from './bulk';
import { del, patch, post, request, toQuery, upload, type SortParam } from './http';
import type { FixedCost, FixedCostUpdate, MenuCategory, MenuCreate, MenuItem, MenuPage, MenuUpdate } from './types';

const BASE = '/web/management/menu';

export type MenuParams = SortParam & { search?: string; category_id?: string; available?: boolean; page?: number; size?: number };

export const menuApi = {
	list: (params: MenuParams): Promise<MenuPage> => request(`${BASE}?${toQuery(params)}`),
	detail: (id: string): Promise<MenuItem> => request(`${BASE}/${id}`),
	categories: (): Promise<MenuCategory[]> => request(`${BASE}/categories`),
	create: (body: MenuCreate): Promise<MenuItem> => post(BASE, body),
	update: (id: string, body: MenuUpdate): Promise<MenuItem> => patch(`${BASE}/${id}`, body),
	remove: (id: string): Promise<void> => del(`${BASE}/${id}`),
	uploadPhoto: (id: string, file: Blob): Promise<MenuItem> => upload(`${BASE}/${id}/photo`, 'file', file),
	fixedCost: {
		of: (id: string): Promise<FixedCost> => request(`${BASE}/${id}/fixed-cost`),
		save: (id: string, body: FixedCostUpdate): Promise<FixedCost> => patch(`${BASE}/${id}/fixed-cost`, body),
		clear: (id: string): Promise<void> => del(`${BASE}/${id}/fixed-cost`)
	},
	bulk: bulkApi<MenuCreate, MenuUpdate>(BASE)
};
