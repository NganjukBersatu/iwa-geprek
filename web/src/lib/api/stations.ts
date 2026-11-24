import { del, patch, post, put, request, toQuery } from './http';
import type { CategoryBranchStation, CategoryStation, ManagedStation, MenuTarget, MenuTargetDetail, MenuTargetPage, StationBranch, StationBranches, StationCreate, StationIntervene, StationMonitor, StationPatch, StationPerformance, StationRoles, StationSetup, StationTask } from './types';

const BASE = '/web/management';

type Branch = { outlet_id?: string | null };
type Period = Branch & { start?: string; end?: string };

export const stationsApi = {
	monitor: (params: Branch): Promise<StationMonitor> => request(`${BASE}/station-monitor?${toQuery(params)}`),
	task: (id: string, params: Branch): Promise<StationTask> => request(`${BASE}/station-tasks/${id}?${toQuery(params)}`),
	intervene: (id: string, body: StationIntervene, params: Branch): Promise<StationTask> => post(`${BASE}/station-tasks/${id}:intervene?${toQuery(params)}`, body),
	performance: (params: Period & { station_id?: string | null }): Promise<StationPerformance> => request(`${BASE}/station-performance?${toQuery(params)}`),
	targets: (params: Period & { search?: string; page?: number; size?: number }): Promise<MenuTargetPage> => request(`${BASE}/menu-targets?${toQuery(params)}`),
	target: (menuId: string, params: Period): Promise<MenuTargetDetail> => request(`${BASE}/menu-targets/${menuId}?${toQuery(params)}`),
	setTarget: (menuId: string, body: MenuTarget): Promise<void> => patch(`${BASE}/menu-targets/${menuId}`, body),
	setBranchTarget: (menuId: string, outletId: string, body: MenuTarget): Promise<void> =>
		patch(`${BASE}/menu-targets/${menuId}/branch-setting?${toQuery({ outlet_id: outletId })}`, body),
	setup: (params: Branch): Promise<StationSetup> => request(`${BASE}/stations?${toQuery(params)}`),
	create: (body: StationCreate): Promise<ManagedStation> => post(`${BASE}/stations`, body),
	update: (id: string, body: StationPatch): Promise<void> => patch(`${BASE}/stations/${id}`, body),
	remove: (id: string): Promise<void> => del(`${BASE}/stations/${id}`),
	branches: (id: string): Promise<StationBranch[]> => request(`${BASE}/stations/${id}/branches`),
	setBranches: (id: string, body: StationBranches): Promise<void> => put(`${BASE}/stations/${id}/branches`, body),
	copyBranches: (id: string, body: { from_outlet_id: string; to_outlet_ids: string[] }): Promise<void> => post(`${BASE}/stations/${id}/branches:copy`, body),
	roles: (id: string): Promise<StationRoles> => request(`${BASE}/stations/${id}/roles`),
	setRoles: (id: string, roleIds: string[]): Promise<void> => put(`${BASE}/stations/${id}/roles`, { role_ids: roleIds }),
	setCategory: (categoryId: string, body: CategoryStation): Promise<void> => patch(`${BASE}/category-stations/${categoryId}`, body),
	setCategoryBranch: (categoryId: string, outletId: string, body: CategoryBranchStation): Promise<void> =>
		patch(`${BASE}/category-stations/${categoryId}/branch-setting?${toQuery({ outlet_id: outletId })}`, body)
};
