import { del, inBranch, patch, post, request, toQuery } from './http';
import type { Device, DeviceCode, DeviceCreate, DeviceDetail, DeviceUpdate, StationOption } from './types';

const BASE = '/web/management/devices';

export const devicesApi = {
	list: (sort?: string): Promise<Device[]> => request(`${BASE}?${toQuery({ sort })}`),
	detail: (id: string): Promise<DeviceDetail> => request(`${BASE}/${id}`),
	create: (outletId: string, body: DeviceCreate): Promise<DeviceCode> => post(inBranch(BASE, outletId), body),
	update: (id: string, body: DeviceUpdate): Promise<DeviceDetail> => patch(`${BASE}/${id}`, body),
	newCode: (id: string): Promise<DeviceCode> => post(`${BASE}/${id}/new-code`, {}),
	revoke: (id: string): Promise<void> => del(`${BASE}/${id}`),
	stations: (outletId: string): Promise<StationOption[]> => request(inBranch(`${BASE}/stations`, outletId))
};
