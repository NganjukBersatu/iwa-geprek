import { put, request } from './http';
import type { CafeSettings, CafeSettingsInput } from './types';

const BASE = '/web/management/cafe-settings';

export const cafeSettingsApi = {
	read: (): Promise<CafeSettings> => request(BASE),
	update: (body: CafeSettingsInput): Promise<CafeSettings> => put(BASE, body)
};
