import { bulkApi } from './bulk';
import { del, patch, post, request, toQuery } from './http';
import type { Permission, Role, RoleCreate, RoleStation, RoleUpdate } from './types';

const BASE = '/web/management/roles';

export const rolesApi = {
	list: (sort?: string): Promise<Role[]> => request(`${BASE}?${toQuery({ sort })}`),
	permissions: (): Promise<Permission[]> => request(`${BASE}/permissions`),
	stations: (): Promise<RoleStation[]> => request(`${BASE}/stations`),
	detail: (id: string): Promise<Role> => request(`${BASE}/${id}`),
	create: (body: RoleCreate): Promise<Role> => post(BASE, body),
	update: (id: string, body: RoleUpdate): Promise<Role> => patch(`${BASE}/${id}`, body),
	remove: (id: string): Promise<void> => del(`${BASE}/${id}`),
	bulk: bulkApi<RoleCreate, RoleUpdate>(BASE)
};
